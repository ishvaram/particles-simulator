from simulation.state import ParticleState

class Particle:
    """A moving particle that bounces off walls."""

    def __init__(self, id, x, y, vx, vy):
        self.id = id
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy

    def step(self, dt, world):
        """Update position and bounce off walls using World bounds."""
        # Move
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Bounce off walls: If hitting wall, clamp position and reverse velocity
        if self.x < 0:
            self.x = 0
            self.vx = -self.vx
        elif self.x > world.width:
            self.x = world.width
            self.vx = -self.vx

        if self.y < 0:
            self.y = 0
            self.vy = -self.vy
        elif self.y > world.height:
            self.y = world.height
            self.vy = -self.vy

    def to_state(self):
        """Create immutable state snapshot for safe publishing. required for pub/sub"""
        return ParticleState(self.id, self.x, self.y, self.vx, self.vy)
