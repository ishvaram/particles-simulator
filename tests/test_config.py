"""Unit tests for configuration loading."""

import pytest
from config import (
    Config,
    SimulationConfig,
    ServerConfig,
    LoggingConfig,
    load_config,
)


class TestSimulationConfig:
    """Tests for SimulationConfig class."""

    def test_default_values(self):
        """SimulationConfig has sensible defaults."""
        config = SimulationConfig()
        assert config.tick_interval == 0.5
        assert config.world_width == 100
        assert config.world_height == 60
        assert config.particle_count == 20

    def test_custom_values(self):
        """SimulationConfig accepts custom values."""
        config = SimulationConfig(
            tick_interval=0.5,
            world_width=200,
            world_height=150,
            particle_count=50
        )
        assert config.tick_interval == 0.5
        assert config.world_width == 200
        assert config.world_height == 150
        assert config.particle_count == 50


class TestServerConfig:
    """Tests for ServerConfig class."""

    def test_default_values(self):
        """ServerConfig has sensible defaults."""
        config = ServerConfig()
        assert config.host == "127.0.0.1"
        assert config.port == 8080

    def test_custom_values(self):
        """ServerConfig accepts custom values."""
        config = ServerConfig(host="0.0.0.0", port=9000)
        assert config.host == "0.0.0.0"
        assert config.port == 9000


class TestLoggingConfig:
    """Tests for LoggingConfig class."""

    def test_default_values(self):
        """LoggingConfig has sensible defaults."""
        config = LoggingConfig()
        assert config.level == "INFO"
        assert config.file == "logs/simulator.log"
        assert config.crash_file == "logs/crash.log"

    def test_custom_values(self):
        """LoggingConfig accepts custom values."""
        config = LoggingConfig(
            level="DEBUG",
            file="/var/log/app.log",
            crash_file="/var/log/crash.log"
        )
        assert config.level == "DEBUG"
        assert config.file == "/var/log/app.log"
        assert config.crash_file == "/var/log/crash.log"


class TestConfig:
    """Tests for main Config class."""

    def test_default_config(self):
        """Config creates default sub-configs."""
        config = Config()
        assert isinstance(config.simulation, SimulationConfig)
        assert isinstance(config.server, ServerConfig)
        assert isinstance(config.logging, LoggingConfig)

    def test_from_dict(self):
        """Config.from_dict parses dictionary."""
        data = {
            "simulation": {"tick_interval": 0.5, "particle_count": 10},
            "server": {"port": 9000},
            "logging": {"level": "DEBUG"}
        }
        config = Config.from_dict(data)
        assert config.simulation.tick_interval == 0.5
        assert config.simulation.particle_count == 10
        assert config.server.port == 9000
        assert config.logging.level == "DEBUG"

    def test_from_dict_partial(self):
        """Config.from_dict handles partial data."""
        data = {"simulation": {"particle_count": 5}}
        config = Config.from_dict(data)
        assert config.simulation.particle_count == 5
        assert config.server.port == 8080  # Default


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_returns_config(self):
        """load_config returns Config object."""
        config = load_config()
        assert isinstance(config, Config)

    def test_load_config_reads_file(self):
        """load_config reads from config.json."""
        config = load_config()
        # Should have values from config.json
        assert config.simulation.tick_interval == 0.5
        assert config.simulation.particle_count == 8

    def test_load_config_missing_file(self, tmp_path):
        """load_config returns defaults for missing file."""
        config = load_config(tmp_path / "nonexistent.json")
        assert isinstance(config, Config)
        assert config.simulation.tick_interval == 0.5  # Default
