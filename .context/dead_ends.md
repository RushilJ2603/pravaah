# dead_ends.md
# ── Approaches Already Ruled Out — DO NOT REVISIT ──────────────
#
# Purpose: This file prevents circular reasoning across sessions.
# Every time an approach is tried and rejected, it is logged here
# with a specific reason. The next AI must read this BEFORE
# suggesting any solutions.
#
# Format:
#   ## [YYYY-MM-DD] — <brief name of approach>
#   **What was tried:** ...
#   **Why rejected:** ... (be specific — not "didn't work")
#   **If user brings it up again:** Remind them of this entry and ask if circumstances changed.

---

## [2026-08-30] — Publishing the database on host port 5432
**What was tried:** `docker-compose.yml` with `ports: - "5432:5432"` for the `db` service.
**Why rejected:** An unrelated container on this machine (`postgres-db`, image `postgres:16`)
already publishes `0.0.0.0:5432`. Docker **silently declines** to publish an already-taken port
rather than erroring: `docker compose up -d` reports success, the container is healthy, and
`docker compose exec db psql` works (unix socket). Meanwhile every host client connects to the
*other* postgres and fails with `password authentication failed for user "pravaah"` — an error
that looks like a credentials bug and is not. Compose now publishes **15432**.
**If user brings it up again:** Do not "fix" the compose file back to 5432 unless the conflicting
container is gone. Verify first with `docker ps -a --format "{{.Names}} | {{.Ports}}" | grep 5432`.
The decisive diagnostic is whether *our* container logs the failed attempt
(`docker compose logs db --since 30s`); if it logs nothing, the traffic never reached it.

---

## [2026-08-30] — Trusting exit codes and in-container psql to prove connectivity
**What was tried:** Two shortcuts for verifying the database was reachable: (a) treating
`docker compose up -d` exit code 0 as proof the stack was up, and (b) running
`psql -h 127.0.0.1 -U pravaah` *inside* the container to prove the password worked.
**Why rejected:** (a) exit code 0 was returned when the Docker daemon was not running at all and
no container was created, and again when the port failed to publish. A pytest run also returned
exit code 0 while reporting `3 skipped` — a skipped gate is not a passing gate. (b) the container's
`pg_hba.conf` has `host all all 127.0.0.1/32 trust`, so an in-container TCP connection is trusted,
never authenticated — it proves nothing about the password.
**If user brings it up again:** Verify with the actual artefact: `docker compose ps` for health,
`docker inspect --format '{{json .NetworkSettings.Ports}}'` for real publishing, a client
connection from the host, and by reading pytest's summary line rather than its exit code.

---

## Template Entry — Replace This
**What was tried:** Using approach X for problem Y  
**Why rejected:** Caused Z issue — specifically, [exact error or failure mode]  
**If user brings it up again:** Ask if the constraint that caused Z has changed before re-exploring.

---
<!-- Add new entries above this line, newest first -->
