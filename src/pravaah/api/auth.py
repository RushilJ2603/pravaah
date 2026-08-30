"""Staff password verification and short-lived bearer authentication.

Implements SOLUTION.md sections 15.3 and 29.5 without adding a crypto
dependency: PBKDF2-HMAC-SHA256 is used for password storage and HMAC-SHA256
signs compact bearer tokens. The signing key comes only from the environment.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import os
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..contracts.api import ErrorCode
from .deps import AppResources
from .schemas import LoginRequest, LoginResponse

router = APIRouter(prefix="/v1/auth", tags=["staff-auth"])

TOKEN_TTL_S = 28_800
PBKDF2_ITERATIONS = 600_000
_HASH_NAME = "sha256"
_DUMMY_HASH = (
    "pbkdf2_sha256$600000$AAAAAAAAAAAAAAAAAAAAAA$"
    "4d-nfYgQyb4x7p5e8uQpycY_kQj8MGOjMYGv9Ts2bEM"
)
_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class StaffIdentity:
    user_id: int
    role: str
    city_id: str


def hash_password(password: str, *, salt: bytes | None = None) -> str:
    """Create the salted password representation stored in ``app_user``."""
    if not password:
        raise ValueError("password must not be empty")
    actual_salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        _HASH_NAME, password.encode("utf-8"), actual_salt, PBKDF2_ITERATIONS
    )
    return "$".join(
        (
            "pbkdf2_sha256",
            str(PBKDF2_ITERATIONS),
            _b64encode(actual_salt),
            _b64encode(digest),
        )
    )


def verify_password(password: str, encoded: str) -> bool:
    """Verify a password without leaking the derived key through comparison."""
    try:
        algorithm, raw_iterations, raw_salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(raw_iterations)
        if iterations < 100_000 or iterations > 2_000_000:
            return False
        actual = hashlib.pbkdf2_hmac(
            _HASH_NAME,
            password.encode("utf-8"),
            _b64decode(raw_salt),
            iterations,
        )
        return hmac.compare_digest(actual, _b64decode(expected))
    except (binascii.Error, TypeError, ValueError):
        return False


def issue_access_token(
    identity: StaffIdentity,
    *,
    secret: bytes | None = None,
    issued_at: datetime | None = None,
) -> str:
    """Issue a signed access token with the binding eight-hour lifetime."""
    current = issued_at or datetime.now(UTC)
    issued = int(current.timestamp())
    payload = {
        "sub": identity.user_id,
        "role": identity.role,
        "city_id": identity.city_id,
        "iat": issued,
        "exp": issued + TOKEN_TTL_S,
    }
    encoded = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(secret or _auth_secret(), encoded.encode("ascii"), hashlib.sha256)
    return f"{encoded}.{_b64encode(signature.digest())}"


def decode_access_token(
    token: str,
    *,
    secret: bytes | None = None,
    current_time: datetime | None = None,
) -> StaffIdentity:
    """Verify a bearer token and return its immutable staff identity."""
    try:
        encoded, signature = token.split(".", 1)
        expected = hmac.new(
            secret or _auth_secret(), encoded.encode("ascii"), hashlib.sha256
        ).digest()
        if not hmac.compare_digest(expected, _b64decode(signature)):
            raise ValueError("invalid signature")
        payload = json.loads(_b64decode(encoded))
        now_epoch = int((current_time or datetime.now(UTC)).timestamp())
        if not isinstance(payload, dict) or int(payload["exp"]) <= now_epoch:
            raise ValueError("token expired")
        if payload["role"] not in {"CONDUCTOR", "OPERATOR"}:
            raise ValueError("invalid role")
        return StaffIdentity(
            user_id=int(payload["sub"]),
            role=str(payload["role"]),
            city_id=str(payload["city_id"]),
        )
    except (binascii.Error, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise _unauthorized("invalid or expired bearer token") from exc


def optional_staff(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> StaffIdentity | None:
    """Authenticate a supplied token and re-check the live staff account."""
    if credentials is None:
        return None
    identity = decode_access_token(credentials.credentials)
    resources: AppResources = request.app.state.resources
    if resources.db_pool is None:
        raise _fail(ErrorCode.FEED_UNAVAILABLE, "authentication store is unavailable", 503)
    with resources.db_pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT role, city_id, agency_id
              FROM app_user
             WHERE user_id = %s AND is_active = TRUE
            """,
            (identity.user_id,),
        )
        row = cur.fetchone()
    if (
        row is None
        or row[0] != identity.role
        or row[1] != identity.city_id
        or identity.city_id != resources.city.city_id
        or (row[2] is not None and row[2] != resources.city.agency_id)
    ):
        raise _unauthorized("staff account is inactive or outside its assigned scope")
    return identity


def require_conductor(
    identity: Annotated[StaffIdentity | None, Depends(optional_staff)],
) -> StaffIdentity:
    """Require a conductor token for a live-state write."""
    if identity is None or identity.role != "CONDUCTOR":
        raise _unauthorized("conductor credentials required")
    return identity


def require_operator(
    identity: Annotated[StaffIdentity | None, Depends(optional_staff)],
) -> StaffIdentity:
    """Require an active operator account for control-room reads."""
    if identity is None:
        raise _unauthorized("operator credentials required")
    if identity.role != "OPERATOR":
        raise _forbidden("operator credentials required")
    return identity


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, request: Request) -> LoginResponse:
    """Exchange an out-of-band staff credential for a short-lived token."""
    resources: AppResources = request.app.state.resources
    if resources.db_pool is None:
        raise _fail(ErrorCode.FEED_UNAVAILABLE, "authentication store is unavailable", 503)

    with resources.db_pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT user_id, password_hash, role, city_id
              FROM app_user
             WHERE username = %s AND is_active = TRUE
            """,
            (body.username,),
        )
        row = cur.fetchone()

    stored = row[1] if row else _DUMMY_HASH
    password_ok = verify_password(body.password, stored)
    if row is None or not password_ok:
        raise _unauthorized("invalid username or password")

    identity = StaffIdentity(user_id=row[0], role=row[2], city_id=row[3])
    if identity.city_id != resources.city.city_id:
        raise _unauthorized("staff account is not valid for this city")
    return LoginResponse(
        access_token=issue_access_token(identity),
        role=identity.role,
        expires_in=TOKEN_TTL_S,
    )


def _auth_secret() -> bytes:
    raw = os.environ.get("PRAVAAH_AUTH_SECRET", "")
    if len(raw.encode("utf-8")) < 32:
        raise _fail(
            ErrorCode.FEED_UNAVAILABLE,
            "staff authentication is not configured",
            503,
        )
    return raw.encode("utf-8")


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _unauthorized(message: str) -> HTTPException:
    return HTTPException(
        status_code=401,
        detail={"code": ErrorCode.INTERNAL.value, "message": message},
        headers={"WWW-Authenticate": "Bearer"},
    )


def _forbidden(message: str) -> HTTPException:
    return HTTPException(
        status_code=403,
        detail={"code": ErrorCode.INTERNAL.value, "message": message},
    )


def _fail(code: ErrorCode, message: str, status: int) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code.value, "message": message})


def provision_user(
    dsn: str,
    *,
    username: str,
    password: str,
    role: str,
    city_id: str,
    agency_id: str | None,
) -> int:
    """Issue one staff credential out of band; there is no HTTP sign-up path."""
    if role not in {"CONDUCTOR", "OPERATOR"}:
        raise ValueError("role must be CONDUCTOR or OPERATOR")
    import psycopg

    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO app_user
                (username, password_hash, role, city_id, agency_id)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING user_id
            """,
            (username, hash_password(password), role, city_id, agency_id),
        )
        user_id = cur.fetchone()[0]
        conn.commit()
    return user_id


def main(argv: list[str] | None = None) -> int:
    """Provision staff from a trusted shell without exposing a signup API."""
    import argparse
    import getpass

    from ..config import active_city, load_settings

    parser = argparse.ArgumentParser(description="Provision a PRAVAAH staff account.")
    parser.add_argument("command", choices=["create-user"])
    parser.add_argument("--username", required=True)
    parser.add_argument("--role", required=True, choices=["CONDUCTOR", "OPERATOR"])
    parser.add_argument("--city", default=None)
    parser.add_argument("--agency", default=None)
    args = parser.parse_args(argv)

    city = active_city()
    password = os.environ.get("PRAVAAH_NEW_USER_PASSWORD") or getpass.getpass(
        "New staff password: "
    )
    user_id = provision_user(
        load_settings().database_dsn,
        username=args.username,
        password=password,
        role=args.role,
        city_id=args.city or city.city_id,
        agency_id=args.agency or city.agency_id,
    )
    print(f"created {args.role} user_id={user_id} username={args.username}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
