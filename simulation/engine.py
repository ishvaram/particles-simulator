import asyncio
import random
import time
from config import load_config
from core.observer import get_logger
from simulation.entities import Particle
from simulation.state import StateSnapshot
from simulation.world import World

class EngineState:
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"

class SimulationEngine:
    def __init__(self, bus, config=None):
        self.bus = bus
        self.config = config or load_config().simulation
        self._lock = asyncio.Lock()
        self._log = get_logger()
        self.world = World(self.config.world_width, self.config.world_height)
        self.tick = 0
        self.sim_time = 0.0
        self._state = EngineState.STOPPED
        self.particles = []
        self._task = None
        self._stop = asyncio.Event()
        self._last_publish_tick = -1
        self.reset()

    @property
    def paused(self):
        return self._state == EngineState.PAUSED

    @property
    def state(self):
        return self._state

    def reset(self):
        self.tick = 0
        self.sim_time = 0.0
        self._last_publish_tick = -1
        width, height = self.world.width, self.world.height
        self.particles = [Particle(f"p{i:02d}", random.uniform(0, width), random.uniform(0, height),
                                   random.uniform(-10, 10), random.uniform(-10, 10))
                          for i in range(self.config.particle_count)]

    async def start(self):
        if self._task:
            return
        self._stop.clear()
        self._state = EngineState.RUNNING
        self._task = asyncio.create_task(self._loop())

    async def stop(self):
        self._stop.set()
        if self._task:
            await self._task
            self._task = None
        self._state = EngineState.STOPPED
        # Notify subscribers of shutdown
        await self.bus.publish({"kind": "engine_stopped", "tick": self.tick})

    async def pause(self):
        async with self._lock:
            self._state = EngineState.PAUSED
            self._log.info(f"engine paused tick={self.tick}")

    async def resume(self):
        async with self._lock:
            self._state = EngineState.RUNNING
            self._log.info(f"engine resumed tick={self.tick}")

    async def get_snapshot(self):
        async with self._lock:
            return StateSnapshot(self.tick, self.sim_time, [particle.to_state() for particle in self.particles])

    async def _loop(self):
        tick_interval = self.config.tick_interval
        next_tick_time = time.perf_counter()
        self._log.info(f"engine start dt={tick_interval}")

        while not self._stop.is_set():
            wait_time = next_tick_time - time.perf_counter()
            if wait_time > 0:
                try:
                    await asyncio.wait_for(self._stop.wait(), timeout=wait_time)
                    break
                except asyncio.TimeoutError:
                    pass
            next_tick_time += tick_interval

            try:
                async with self._lock:
                    if self._state == EngineState.RUNNING:
                        for particle in self.particles:
                            particle.step(tick_interval, self.world)
                        self.tick += 1
                        self.sim_time += tick_interval
                    snapshot = StateSnapshot(self.tick, self.sim_time, [particle.to_state() for particle in self.particles])
            except Exception as exc:
                self._log.error("tick fail", err=exc)
                continue

            # Only publish if state changed (avoid flooding when paused)
            if self.tick != self._last_publish_tick:
                try:
                    await self.bus.publish(snapshot)
                    self._last_publish_tick = self.tick
                except Exception:
                    pass

        self._log.info(f"engine stop tick={self.tick}")
