"""Settings and configuration management."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings loaded from configuration file and environment."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize settings.

        Args:
            config_path: Path to configuration file. If None, uses default locations.
        """
        self.config_path = self._resolve_config_path(config_path)
        self._config: Dict[str, Any] = {}
        self.load()

    def _resolve_config_path(self, config_path: Optional[str]) -> Path:
        """Resolve configuration file path."""
        if config_path:
            return Path(config_path)

        # Try environment variable
        env_path = os.getenv("OVERMIND_CONFIG")
        if env_path:
            return Path(env_path)

        # Try default locations
        default_paths = [
            Path("overmind.conf"),
            Path("/etc/overmind/overmind.conf"),
            Path.home() / ".config" / "overmind" / "overmind.conf",
        ]

        for path in default_paths:
            if path.exists():
                return path

        # Return first default if none exist
        return default_paths[0]

    def load(self) -> None:
        """Load configuration from file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, "r") as f:
            self._config = yaml.safe_load(f) or {}

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            key: Configuration key (supports dot notation, e.g., 'weather.api_key')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

            if value is None:
                return default

        return value

    @property
    def weather_api_key(self) -> str:
        """Get weather API key."""
        return os.getenv("WEATHER_API_KEY") or self.get("weather.api_key", "")

    @property
    def location_id(self) -> int:
        """Get location ID."""
        return self.get("weather.location.id", 0)

    @property
    def location_name(self) -> str:
        """Get location name."""
        return self.get("weather.location.name", "Unknown")

    @property
    def wattrouter_url(self) -> str:
        """Get Wattrouter device URL."""
        return os.getenv("WATTROUTER_URL") or self.get("wattrouter.url", "http://192.168.1.1")

    @property
    def wattrouter_username(self) -> str:
        """Get Wattrouter username."""
        return os.getenv("WATTROUTER_USERNAME") or self.get("wattrouter.username", "admin")

    @property
    def wattrouter_password(self) -> str:
        """Get Wattrouter password."""
        return os.getenv("WATTROUTER_PASSWORD") or self.get("wattrouter.password", "")

    def __repr__(self) -> str:
        """String representation."""
        return f"Settings(config_path={self.config_path})"
