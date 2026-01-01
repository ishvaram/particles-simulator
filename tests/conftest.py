"""Pytest fixtures for all tests."""

import pytest
from httpx import AsyncClient, ASGITransport

from ui.app import create_app
from communication.bus import EventBus
from simulation.engine import SimulationEngine
from simulation.world import World
from simulation.entities import Particle
from config import SimulationConfig


@pytest.fixture
def world():
    """Create a test world."""
    return World(width=100, height=60)


@pytest.fixture
def particle():
    """Create a test particle."""
    return Particle(id="p01", x=50, y=30, vx=10, vy=-5)


@pytest.fixture
def sim_config():
    """Create test simulation config."""
    return SimulationConfig(
        tick_interval=0.1,
        world_width=100,
        world_height=60,
        particle_count=5
    )


@pytest.fixture
async def bus():
    """Create test event bus."""
    return EventBus(default_queue_size=10)


@pytest.fixture
async def engine(bus, sim_config):
    """Create test simulation engine."""
    eng = SimulationEngine(bus=bus, config=sim_config)
    yield eng
    if eng._task:
        await eng.stop()


@pytest.fixture
async def app():
    """Create test FastAPI app."""
    return create_app()


@pytest.fixture
async def client(app):
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
