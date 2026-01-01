"""Unit tests for simulation components."""

import pytest
from simulation.world import World
from simulation.entities import Particle
from simulation.state import ParticleState, StateSnapshot


class TestWorld:
    """Tests for World class."""

    def test_world_creation(self):
        """World stores width and height."""
        world = World(width=100, height=60)
        assert world.width == 100
        assert world.height == 60

    def test_world_different_sizes(self):
        """World handles various sizes."""
        world = World(width=200, height=150)
        assert world.width == 200
        assert world.height == 150


class TestParticle:
    """Tests for Particle class."""

    def test_particle_creation(self):
        """Particle stores initial state."""
        p = Particle(id="p01", x=50, y=30, vx=10, vy=-5)
        assert p.id == "p01"
        assert p.x == 50
        assert p.y == 30
        assert p.vx == 10
        assert p.vy == -5

    def test_particle_step_movement(self):
        """Particle moves based on velocity."""
        world = World(100, 60)
        p = Particle(id="p01", x=50, y=30, vx=10, vy=-5)
        p.step(dt=1.0, world=world)
        assert p.x == 60  # 50 + 10*1
        assert p.y == 25  # 30 + (-5)*1

    def test_particle_bounce_left_wall(self):
        """Particle bounces off left wall."""
        world = World(100, 60)
        p = Particle(id="p01", x=5, y=30, vx=-10, vy=0)
        p.step(dt=1.0, world=world)
        assert p.x == 0  # Clamped to wall
        assert p.vx == 10  # Velocity reversed

    def test_particle_bounce_right_wall(self):
        """Particle bounces off right wall."""
        world = World(100, 60)
        p = Particle(id="p01", x=95, y=30, vx=10, vy=0)
        p.step(dt=1.0, world=world)
        assert p.x == 100  # Clamped to wall
        assert p.vx == -10  # Velocity reversed

    def test_particle_bounce_top_wall(self):
        """Particle bounces off top wall (y=0)."""
        world = World(100, 60)
        p = Particle(id="p01", x=50, y=5, vx=0, vy=-10)
        p.step(dt=1.0, world=world)
        assert p.y == 0  # Clamped to wall
        assert p.vy == 10  # Velocity reversed

    def test_particle_bounce_bottom_wall(self):
        """Particle bounces off bottom wall."""
        world = World(100, 60)
        p = Particle(id="p01", x=50, y=55, vx=0, vy=10)
        p.step(dt=1.0, world=world)
        assert p.y == 60  # Clamped to wall
        assert p.vy == -10  # Velocity reversed

    def test_particle_to_state(self):
        """Particle converts to immutable state."""
        p = Particle(id="p01", x=50, y=30, vx=10, vy=-5)
        state = p.to_state()
        assert isinstance(state, ParticleState)
        assert state.id == "p01"
        assert state.x == 50
        assert state.y == 30


class TestParticleState:
    """Tests for ParticleState class."""

    def test_particle_state_creation(self):
        """ParticleState stores values."""
        state = ParticleState(id="p01", x=50, y=30, vx=10, vy=-5)
        assert state.id == "p01"
        assert state.x == 50

    def test_particle_state_uses_slots(self):
        """ParticleState uses __slots__ for memory efficiency."""
        assert hasattr(ParticleState, "__slots__")


class TestStateSnapshot:
    """Tests for StateSnapshot class."""

    def test_snapshot_creation(self):
        """StateSnapshot stores tick and particles."""
        particles = [ParticleState("p01", 10, 20, 1, 2)]
        snap = StateSnapshot(tick=100, time=50.0, particles=particles)
        assert snap.tick == 100
        assert snap.time == 50.0
        assert len(snap.particles) == 1

    def test_snapshot_has_ksuid(self):
        """StateSnapshot generates KSUID."""
        snap = StateSnapshot(tick=1, time=0.5, particles=[])
        assert snap.id is not None
        assert len(snap.id) > 0

    def test_snapshot_has_timestamp(self):
        """StateSnapshot generates timestamp."""
        snap = StateSnapshot(tick=1, time=0.5, particles=[])
        assert snap.timestamp is not None
        assert "T" in snap.timestamp  # ISO format

    def test_snapshot_to_dict(self):
        """StateSnapshot converts to dict."""
        particles = [ParticleState("p01", 10, 20, 1, 2)]
        snap = StateSnapshot(tick=100, time=50.0, particles=particles)
        d = snap.to_dict()
        assert d["tick"] == 100
        assert d["sim_time_s"] == 50.0
        assert len(d["particles"]) == 1
        assert d["particles"][0]["id"] == "p01"

    def test_snapshot_uses_slots(self):
        """StateSnapshot uses __slots__ for memory efficiency."""
        assert hasattr(StateSnapshot, "__slots__")
