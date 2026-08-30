"""FastAPI application.

Implements SOLUTION.md section 14.1 (one FastAPI app serving the passenger and
admin APIs) and section 12.4's response principles.

Errors use the single shape from section 29.4 so a client has exactly one error
contract to handle, whether the failure came from a handler or from FastAPI's
own validation.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..contracts.api import ErrorCode
from . import passenger
from .deps import build_resources, now
from .schemas import HealthResponse

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.resources = build_resources()
    log.info("started for city %s", app.state.resources.city.city_id)
    yield
    app.state.resources.close()


app = FastAPI(
    title="PRAVAAH",
    version="0.1.0",
    summary="Intelligent public transport crowding and route prediction",
    lifespan=lifespan,
)

# The frontend is served from the same origin in the deploy profile (section 14.4),
# so this matters only for local development against a Vite dev server.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(passenger.router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Render every HTTPException in the section 29.4 error shape."""
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail:
        body = {"code": detail["code"], "message": detail.get("message", "")}
    else:
        body = {"code": _code_for_status(exc.status_code), "message": str(detail)}
    return JSONResponse(status_code=exc.status_code, content={"error": body})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """FastAPI's own validation errors, in our shape rather than its default.

    A missing required `bbox` lands here, and section 29.2 says that is an
    INVALID_COORDINATES error -- never a full-fleet response.
    """
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": ErrorCode.INVALID_COORDINATES.value,
                "message": "; ".join(
                    f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()
                ),
            }
        },
    )


def _code_for_status(status: int) -> str:
    return {
        404: ErrorCode.NO_ROUTE_FOUND.value,
        429: ErrorCode.RATE_LIMITED.value,
        503: ErrorCode.FEED_UNAVAILABLE.value,
    }.get(status, ErrorCode.INTERNAL.value)


@app.get("/v1/health", response_model=HealthResponse, tags=["ops"])
def health(request: Request) -> HealthResponse:
    """Dependency reachability, for the deployment runbook (section 14.4).

    Reports `degraded` rather than failing when a dependency is down: section
    16.1 requires the system to degrade visibly, and an endpoint that returns
    500 cannot say which dependency is at fault.
    """
    resources = request.app.state.resources
    database = resources.database_ok()
    redis = resources.redis_ok()

    tracked = 0
    feed_version_id = None
    if redis:
        try:
            tracked = resources.state.count()
        except Exception:  # noqa: BLE001
            redis = False
    if database:
        try:
            with resources.db_pool.connection() as conn, conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT feed_version_id FROM feed_version
                     WHERE city_id = %s ORDER BY imported_at DESC LIMIT 1
                    """,
                    (resources.city.city_id,),
                )
                row = cur.fetchone()
                feed_version_id = row[0] if row else None
        except Exception:  # noqa: BLE001
            database = False

    return HealthResponse(
        status="ok" if (database and redis) else "degraded",
        city_id=resources.city.city_id,
        generated_at=now(),
        database=database,
        redis=redis,
        vehicles_tracked=tracked,
        feed_version_id=feed_version_id,
    )
