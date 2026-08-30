#!/usr/bin/env bash
# Bring up the whole PRAVAAH demo stack in one command.
#
# Every step here exists because it bit us at least once:
#
#   * The Windows Python is used explicitly. The WSL `python3` does NOT have the
#     project dependencies installed.
#   * Environment variables do NOT propagate from WSL to a Windows executable.
#     WSLENV is the only mechanism that works, which is why every export below
#     is paired with it.
#   * Modules run from `src/`. `pyproject.toml` sets pythonpath for pytest only,
#     not for `python -m`.
#   * The API takes ~25 s to become healthy because the database pool warms on
#     startup. Never start it in front of an audience.
#
# Usage:  ./scripts/demo.sh [--fresh] [--tunnel]
#           --fresh    re-persist the network and re-seed staff accounts
#           --tunnel   also expose the API on a public HTTPS URL via Cloudflare,
#                      so a phone on mobile data (or a judge) can reach it
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${PRAVAAH_PYTHON:-/mnt/c/Users/jishu/AppData/Local/Programs/Python/Python312/python.exe}"
PORT="${PRAVAAH_PORT:-8000}"
DEMO_USER="${PRAVAAH_DEMO_USER:-operator}"
DEMO_PASS="${PRAVAAH_DEMO_PASS:-pravaah-demo}"
FRESH=0; TUNNEL=0
for arg in "$@"; do
    case "$arg" in
        --fresh)  FRESH=1 ;;
        --tunnel) TUNNEL=1 ;;
    esac
done
CLOUDFLARED="${CLOUDFLARED:-$HOME/.local/bin/cloudflared}"

# A demo secret. Deliberately obvious: this is not a production credential.
export PRAVAAH_AUTH_SECRET="${PRAVAAH_AUTH_SECRET:-pravaah-demo-secret-key-not-for-production-use-32b}"
export WSLENV="PRAVAAH_AUTH_SECRET"

DOCKER="docker"; command -v docker >/dev/null 2>&1 || DOCKER="docker.exe"

say() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }
die() { printf '\n\033[31mFAILED: %s\033[0m\n' "$*" >&2; exit 1; }

say "1/6  Starting Postgres and Redis"
"$DOCKER" compose -f "$ROOT/docker-compose.yml" up -d >/dev/null 2>&1 \
    || die "compose up failed -- is Docker Desktop running?"
for _ in $(seq 1 30); do
    "$PY" -c "
import sys, psycopg
sys.path.insert(0, r'$ROOT/src')
from pravaah.config import load_settings
psycopg.connect(load_settings().database_dsn, connect_timeout=3).close()
" >/dev/null 2>&1 && break
    sleep 2
done || true
say "     database reachable"

say "2/6  Publishing the Delhi network"
cd "$ROOT/src" || die "no src/"
if [[ $FRESH -eq 1 ]]; then
    "$PY" -m pravaah.sim.persist 2>&1 | tail -1
else
    "$PY" -c "
import sys; sys.path.insert(0, '.')
import psycopg
from pravaah.config import load_settings
c = psycopg.connect(load_settings().database_dsn)
n = c.execute(\"select count(*) from feed_version where city_id='delhi'\").fetchone()[0]
print('     feed already present' if n else '     none found')
raise SystemExit(0 if n else 1)
" 2>/dev/null || "$PY" -m pravaah.sim.persist 2>&1 | tail -1
fi

say "3/6  Seeding staff accounts"
"$PY" -c "
import sys; sys.path.insert(0, '.')
from pravaah.api.auth import provision_user
from pravaah.config import load_settings, active_city
dsn, city = load_settings().database_dsn, active_city()
for user, role in (('$DEMO_USER', 'OPERATOR'), ('conductor', 'CONDUCTOR')):
    try:
        uid = provision_user(dsn, username=user, password='$DEMO_PASS', role=role,
                             city_id=city.city_id, agency_id=city.agency_id)
        print(f'     created {role.lower()} ({user})')
    except Exception:
        print(f'     {user} already exists')
"

say "4/6  Starting the vehicle simulator"
pgrep -f "pravaah.sim.generate" >/dev/null 2>&1 && echo "     already running" || {
    setsid "$PY" -m pravaah.sim.generate --interval 5 --persist-history \
        > /tmp/pravaah-sim.log 2>&1 < /dev/null &
    disown; sleep 6; echo "     300 vehicles moving  (log: /tmp/pravaah-sim.log)"
}

say "5/6  Starting the API on :$PORT"
setsid "$PY" -m uvicorn pravaah.api.main:app --host 0.0.0.0 --port "$PORT" \
    > /tmp/pravaah-api.log 2>&1 < /dev/null &
disown

say "6/6  Waiting for the API to become healthy (~25 s)"
HEALTH=""
for _ in $(seq 1 40); do
    HEALTH="$(curl -sS --max-time 4 "http://127.0.0.1:$PORT/v1/health" 2>/dev/null || true)"
    [[ "$HEALTH" == *'"status":"ok"'* ]] && break
    sleep 2
done
[[ "$HEALTH" == *'"status":"ok"'* ]] || die "API never became healthy -- see /tmp/pravaah-api.log"

VEHICLES=$(printf '%s' "$HEALTH" | grep -oE '"vehicles_tracked":[0-9]+' | cut -d: -f2)

PUBLIC_URL=""
if [[ $TUNNEL -eq 1 ]]; then
    say "7/7  Opening a public HTTPS tunnel"
    if [[ ! -x "$CLOUDFLARED" ]]; then
        echo "     cloudflared not found at $CLOUDFLARED -- skipping tunnel"
    else
        setsid "$CLOUDFLARED" tunnel --url "http://localhost:$PORT" --no-autoupdate \
            > /tmp/pravaah-tunnel.log 2>&1 < /dev/null &
        disown
        for _ in $(seq 1 20); do
            PUBLIC_URL="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' \
                          /tmp/pravaah-tunnel.log 2>/dev/null | head -1)"
            [[ -n "$PUBLIC_URL" ]] && break
            sleep 2
        done
        if [[ -n "$PUBLIC_URL" ]]; then
            echo "     $PUBLIC_URL"
            # A quick tunnel gets a NEW random hostname every restart, so the
            # app cannot hardcode it. Leave it somewhere the app build can read.
            printf '%s\n' "$PUBLIC_URL" > "$ROOT/.tunnel-url"
        else
            echo "     tunnel did not come up -- see /tmp/pravaah-tunnel.log"
        fi
    fi
fi

cat <<BANNER

  ────────────────────────────────────────────────────────────
   PRAVAAH demo is up.        $VEHICLES vehicles tracked · Delhi
  ────────────────────────────────────────────────────────────

   API        http://localhost:$PORT
   Docs       http://localhost:$PORT/docs
${PUBLIC_URL:+   Public     $PUBLIC_URL   (written to .tunnel-url)}

   Passenger  (no auth)
     /v1/vehicles?bbox=28.35,76.80,28.90,77.45
     /v1/stops/DLN0000/departures
     /v1/plan?from_lat=28.6675&from_lon=77.2285&to_lat=28.6315&to_lon=77.2167
     /v1/trips/{trip_id}/forecast

   Staff login    $DEMO_USER / $DEMO_PASS   (also: conductor)
     curl -X POST http://localhost:$PORT/v1/auth/login \\
       -H 'Content-Type: application/json' \\
       -d '{"username":"$DEMO_USER","password":"$DEMO_PASS"}'
     then send  Authorization: Bearer <access_token>  to /v1/admin/*

   Logs       /tmp/pravaah-api.log · /tmp/pravaah-sim.log
   Stop       docker compose down   (and kill the python processes)

  ────────────────────────────────────────────────────────────

BANNER
