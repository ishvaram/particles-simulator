import json
from pathlib import Path

_DEFAULT_CONFIG = Path(__file__).parent / "config.json"


class SimulationConfig:
    __slots__ = ("tick_interval", "world_width", "world_height", "particle_count")
    
    def __init__(self, tick_interval=0.5, world_width=100, world_height=60, particle_count=20):
        self.tick_interval = tick_interval
        self.world_width = world_width
        self.world_height = world_height
        self.particle_count = particle_count


class ServerConfig:
    __slots__ = ("host", "port")
    
    def __init__(self, host="127.0.0.1", port=8080):
        self.host = host
        self.port = port


class LoggingConfig:
    __slots__ = ("level", "file", "crash_file")
    
    def __init__(self, level="INFO", file="logs/simulator.log", crash_file="logs/crash.log"):
        self.level = level
        self.file = file
        self.crash_file = crash_file


class Config:
    __slots__ = ("simulation", "server", "logging")
    
    def __init__(self, simulation=None, server=None, logging=None):
        self.simulation = simulation or SimulationConfig()
        self.server = server or ServerConfig()
        self.logging = logging or LoggingConfig()

    @classmethod
    def from_dict(cls, d):
        return cls(
            SimulationConfig(**d.get("simulation", {})),
            ServerConfig(**d.get("server", {})),
            LoggingConfig(**d.get("logging", {})),
        )


def load_config(path=None):
    config_path = Path(path) if path else _DEFAULT_CONFIG
    
    if not config_path.exists():
        return Config()
    
    with open(config_path) as file:
        return Config.from_dict(json.load(file))
