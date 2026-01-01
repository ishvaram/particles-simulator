from utils.ksuid import generate_ksuid
from utils.timestamp import format_timestamp


class ParticleState:
    __slots__ = ("id", "x", "y", "vx", "vy")
    def __init__(self, id, x, y, vx, vy):
        self.id, self.x, self.y, self.vx, self.vy = id, x, y, vx, vy


class StateSnapshot:
    __slots__ = ("id", "timestamp", "tick", "time", "particles")

    def __init__(self, tick, time, particles, id=None, timestamp=None):
        self.id = id or generate_ksuid()
        self.timestamp = timestamp or format_timestamp()
        self.tick = tick
        self.time = time
        self.particles = particles

    @property
    def sim_time_s(self):  # compat
        return self.time

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "tick": self.tick,
            "sim_time_s": self.time,
            "particles": [{"id": p.id, "x": p.x, "y": p.y, "vx": p.vx, "vy": p.vy} for p in self.particles]
        }
