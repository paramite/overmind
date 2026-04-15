"""Tests for configuration settings."""

import os
import pytest
from overmind.config.settings import Settings


class TestSettings:
    """Test Settings class."""

    def test_load_config_from_path(self, test_config_path):
        """Test loading configuration from specified path."""
        settings = Settings(str(test_config_path))
        assert settings.weather_api_key == "test_api_key"
        assert settings.location_id == 3070720
        assert settings.location_name == "Mikulov"

    def test_get_with_dot_notation(self, test_config_path):
        """Test getting nested values with dot notation."""
        settings = Settings(str(test_config_path))
        assert settings.get("weather.location.coord.lat") == 48.805561
        assert settings.get("weather.location.coord.lon") == 16.6378

    def test_get_with_default(self, test_config_path):
        """Test getting value with default fallback."""
        settings = Settings(str(test_config_path))
        assert settings.get("nonexistent.key", "default") == "default"
        assert settings.get("weather.nonexistent", 999) == 999

    def test_wattrouter_properties(self, test_config_path):
        """Test Wattrouter configuration properties."""
        settings = Settings(str(test_config_path))
        assert settings.wattrouter_url == "http://192.168.1.100"
        assert settings.wattrouter_username == "admin"
        assert settings.wattrouter_password == "test_password"

    def test_environment_override(self, test_config_path, monkeypatch):
        """Test that environment variables override config file."""
        monkeypatch.setenv("WEATHER_API_KEY", "env_api_key")
        monkeypatch.setenv("WATTROUTER_URL", "http://192.168.2.200")

        settings = Settings(str(test_config_path))
        assert settings.weather_api_key == "env_api_key"
        assert settings.wattrouter_url == "http://192.168.2.200"

    def test_config_file_not_found(self, tmp_path):
        """Test error when configuration file doesn't exist."""
        nonexistent = tmp_path / "nonexistent.conf"
        with pytest.raises(FileNotFoundError):
            Settings(str(nonexistent))
