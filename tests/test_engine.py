"""Unit tests for SimulationEngine."""

import asyncio
import pytest
from communication.bus import EventBus
from simulation.engine import SimulationEngine
from simulation.state import StateSnapshot
from config import SimulationConfig


class TestSimulationEngine:
    """Tests for SimulationEngine class."""

    @pytest.mark.asyncio
    async def test_engine_creation(self):
        """Engine initializes with config."""
        bus = EventBus(queue_size=10)
        config = SimulationConfig(particle_count=5)
        engine = SimulationEngine(bus=bus, config=config)
        
        assert engine.tick == 0
        assert engine.paused is False
        assert len(engine.particles) == 5

    @pytest.mark.asyncio
    async def test_engine_start_stop(self):
        """Engine starts and stops cleanly."""
        bus = EventBus(queue_size=10)
        config = SimulationConfig(tick_interval=0.05, particle_count=3)
        engine = SimulationEngine(bus=bus, config=config)
        
        await engine.start()
        assert engine._task is not None
        
        await asyncio.sleep(0.1)  # Let it run a bit
        
        await engine.stop()
        assert engine._stop.is_set()

    @pytest.mark.asyncio
    async def test_engine_tick_advances(self):
        """Engine tick advances over time."""
        bus = EventBus(queue_size=10)
        config = SimulationConfig(tick_interval=0.05, particle_count=3)
        engine = SimulationEngine(bus=bus, config=config)
        
        await engine.start()
        await asyncio.sleep(0.15)  # Should get ~3 ticks
        await engine.stop()
        
        assert engine.tick >= 2

    @pytest.mark.asyncio
    async def test_engine_pause_resume(self):
        """Engine can be paused and resumed."""
        bus = EventBus(queue_size=10)
        config = SimulationConfig(tick_interval=0.05, particle_count=3)
        engine = SimulationEngine(bus=bus, config=config)
        
        await engine.start()
        await asyncio.sleep(0.1)
        
        await engine.pause()
        assert engine.paused is True
        tick_at_pause = engine.tick
        
        await asyncio.sleep(0.1)
        assert engine.tick == tick_at_pause  # Tick shouldn't advance
        
        await engine.resume()
        assert engine.paused is False
        
        await asyncio.sleep(0.1)
        assert engine.tick > tick_at_pause  # Tick should advance again
        
        await engine.stop()

    @pytest.mark.asyncio
    async def test_engine_reset(self):
        """Engine reset restores initial state."""
        bus = EventBus(queue_size=10)
        config = SimulationConfig(tick_interval=0.05, particle_count=3)
        engine = SimulationEngine(bus=bus, config=config)
        
        await engine.start()
        await asyncio.sleep(0.1)
        
        engine.reset()
        
        assert engine.tick == 0
        assert engine.sim_time == 0
        assert len(engine.particles) == 3
        
        await engine.stop()

    @pytest.mark.asyncio
    async def test_engine_get_snapshot(self):
        """Engine returns current state snapshot."""
        bus = EventBus(queue_size=10)
        config = SimulationConfig(particle_count=5)
        engine = SimulationEngine(bus=bus, config=config)
        
        snapshot = await engine.get_snapshot()
        
        assert isinstance(snapshot, StateSnapshot)
        assert snapshot.tick == 0
        assert len(snapshot.particles) == 5

    @pytest.mark.asyncio
    async def test_engine_publishes_to_bus(self):
        """Engine publishes snapshots to event bus."""
        bus = EventBus(queue_size=10)
        config = SimulationConfig(tick_interval=0.05, particle_count=3)
        engine = SimulationEngine(bus=bus, config=config)
        
        sub = await bus.subscribe("test-client")
        
        await engine.start()
        
        # Wait for at least one message
        msg = await asyncio.wait_for(sub.queue.get(), timeout=1.0)
        
        await engine.stop()
        
        assert isinstance(msg, StateSnapshot)
        assert len(msg.particles) == 3

    @pytest.mark.asyncio
    async def test_engine_particles_move(self):
        """Particles change position over time."""
        bus = EventBus(queue_size=10)
        config = SimulationConfig(tick_interval=0.05, particle_count=3)
        engine = SimulationEngine(bus=bus, config=config)
        
        initial_positions = [(p.x, p.y) for p in engine.particles]
        
        await engine.start()
        await asyncio.sleep(0.2)
        await engine.stop()
        
        final_positions = [(p.x, p.y) for p in engine.particles]
        
        # At least some particles should have moved
        moved = sum(1 for i, f in zip(initial_positions, final_positions) if i != f)
        assert moved > 0
