"""Configuration management for ace-connection-logger."""

import os
from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG = {
    "monitoring": {
        "interval_seconds": 60,  # Check every minute
        "ping_count": 5,  # Number of pings per check
        "timeout_seconds": 2,  # Timeout for each ping
    },
    "hosts": [
        {"name": "Google DNS", "address": "8.8.8.8"},
        {"name": "Cloudflare DNS", "address": "1.1.1.1"},
        {"name": "Local Gateway", "address": "192.168.1.1"},
    ],
    "database": {
        "path": "connection_logs.db",
        "retention_days": 90,
    },
    "dashboard": {
        "port": 8501,
        "host": "localhost",
    },
}


class Config:
    """Configuration manager for the application."""

    def __init__(self, config_path: str | None = None):
        """Initialize configuration.

        Args:
            config_path: Path to configuration file. If None, uses default location.
        """
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), "config.yaml"
            )

        self.config_path = Path(config_path)
        self._config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from file or return defaults.

        Returns:
            Configuration dictionary.
        """
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    config = yaml.safe_load(f)
                    # Merge with defaults to ensure all keys exist
                    return self._merge_configs(DEFAULT_CONFIG.copy(), config)
            except Exception as e:
                print(f"Error loading config from {self.config_path}: {e}")
                print("Using default configuration")
                return DEFAULT_CONFIG.copy()
        else:
            return DEFAULT_CONFIG.copy()

    def _merge_configs(
        self, base: dict[str, Any], override: dict[str, Any]
    ) -> dict[str, Any]:
        """Recursively merge two configuration dictionaries.

        Args:
            base: Base configuration dictionary.
            override: Configuration to merge into base.

        Returns:
            Merged configuration dictionary.
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                base[key] = self._merge_configs(base[key], value)
            else:
                base[key] = value
        return base

    def save_default(self) -> None:
        """Save default configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False, sort_keys=False)

    @property
    def monitoring_interval(self) -> int:
        """Get monitoring interval in seconds."""
        return self._config["monitoring"]["interval_seconds"]

    @property
    def ping_count(self) -> int:
        """Get number of pings per check."""
        return self._config["monitoring"]["ping_count"]

    @property
    def ping_timeout(self) -> int:
        """Get ping timeout in seconds."""
        return self._config["monitoring"]["timeout_seconds"]

    @property
    def hosts(self) -> list[dict[str, str]]:
        """Get list of hosts to monitor."""
        return self._config["hosts"]

    @property
    def database_path(self) -> str:
        """Get database file path."""
        return self._config["database"]["path"]

    @property
    def retention_days(self) -> int:
        """Get data retention period in days."""
        return self._config["database"]["retention_days"]

    @property
    def dashboard_port(self) -> int:
        """Get dashboard port."""
        return self._config["dashboard"]["port"]

    @property
    def dashboard_host(self) -> str:
        """Get dashboard host."""
        return self._config["dashboard"]["host"]
