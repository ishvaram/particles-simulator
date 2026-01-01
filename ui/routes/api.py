"""API routes for stats and subscribers."""

from fastapi import APIRouter, Depends

from utils.timestamp import format_timestamp
from ui.auth import verify_basic_auth

router = APIRouter(prefix="/api/v1", tags=["api"])

# These will be set by app.py
_engine = None
_bus = None
_file_logger = None


def init(engine, bus, file_logger):
    """Initialize with engine, bus, and logger references."""
    global _engine, _bus, _file_logger
    _engine = engine
    _bus = bus
    _file_logger = file_logger


@router.get("/stats")
async def stats(username=Depends(verify_basic_auth)):
    """Return bus and simulation statistics (requires basic auth)."""
    bus_stats = _bus.get_stats()
    snapshot = await _engine.get_snapshot()
    logger_stats = _file_logger.get_stats()
    return {
        "timestamp": format_timestamp(),
        "simulation": {
            "tick": snapshot.tick,
            "sim_time_s": snapshot.sim_time_s,
            "entity_count": len(snapshot.particles),
            "paused": _engine.paused,
        },
        "bus": bus_stats,
        "logger": logger_stats,
    }


@router.get("/subscribers")
async def subscribers(username=Depends(verify_basic_auth)):
    """Return info about all current subscribers (requires basic auth)."""
    return await _bus.get_subscriber_info()
