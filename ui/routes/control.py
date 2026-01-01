"""Simulation control routes."""

import time

from fastapi import APIRouter, Depends

from ui.auth import verify_basic_auth

router = APIRouter(prefix="/api/v1/control", tags=["control"])

# These will be set by app.py
_engine = None
_bus = None


def init(engine, bus):
    """Initialize with engine and bus references."""
    global _engine, _bus
    _engine = engine
    _bus = bus


@router.post("/pause")
async def pause(username=Depends(verify_basic_auth)):
    """Pause simulation (requires basic auth)."""
    await _engine.pause()
    await _bus.publish({"kind": "paused", "timestamp": time.time()})
    return {"ok": True}


@router.post("/resume")
async def resume(username=Depends(verify_basic_auth)):
    """Resume simulation (requires basic auth)."""
    await _engine.resume()
    await _bus.publish({"kind": "resumed", "timestamp": time.time()})
    return {"ok": True}


@router.post("/reset")
async def reset(username=Depends(verify_basic_auth)):
    """Reset simulation (requires basic auth)."""
    _engine.reset()
    await _bus.publish({"kind": "reset", "timestamp": time.time()})
    return {"ok": True}
