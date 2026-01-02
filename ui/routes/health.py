"""Health and observability routes."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from internal.health import Status
from utils.timestamp import format_timestamp

router = APIRouter(prefix="/api/v1", tags=["health"])

# These will be set by app.py
_engine = None
_health_checker = None


def init(engine, health_checker):
    """Initialize with engine and health checker references."""
    global _engine, _health_checker
    _engine = engine
    _health_checker = health_checker


@router.get("/health")
async def health():
    """Health check with component status."""
    report = await _health_checker.check()
    status_code = 200 if report.status != Status.FAIL else 503
    return JSONResponse(content=report.to_dict(), status_code=status_code)


@router.get("/heartbeat")
async def heartbeat():
    """Lightweight heartbeat for frequent polling."""
    snapshot = await _engine.get_snapshot()
    return {
        "status": "ok",
        "timestamp": format_timestamp(),
        "tick": snapshot.tick,
        "uptime_s": snapshot.sim_time_s,
        "engine_state": _engine.state,
    }


