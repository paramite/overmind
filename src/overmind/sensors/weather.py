"""Weather service for checking current conditions."""

from typing import Dict, Optional
from enum import Enum

import requests


class WeatherCondition(Enum):
    """Weather condition categories."""
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    SNOW = "snow"
    UNKNOWN = "unknown"


class WeatherService:
    """Client for fetching weather data from OpenWeatherMap API."""

    def __init__(self, api_key: str, location_id: Optional[int] = None,
                 lat: Optional[float] = None, lon: Optional[float] = None):
        """
        Initialize weather service.

        Args:
            api_key: OpenWeatherMap API key
            location_id: City ID (optional, alternative to lat/lon)
            lat: Latitude (optional, alternative to location_id)
            lon: Longitude (optional, alternative to location_id)
        """
        self.api_key = api_key
        self.location_id = location_id
        self.lat = lat
        self.lon = lon
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"

    def get_current_weather(self) -> Dict:
        """
        Fetch current weather data.

        Returns:
            Dictionary with weather data

        Raises:
            requests.RequestException: On API error
        """
        params = {"appid": self.api_key, "units": "metric"}

        if self.location_id:
            params["id"] = self.location_id
        elif self.lat and self.lon:
            params["lat"] = self.lat
            params["lon"] = self.lon
        else:
            raise ValueError("Either location_id or (lat, lon) must be provided")

        response = requests.get(self.base_url, params=params, timeout=10)
        response.raise_for_status()

        return response.json()

    def is_sunny(self, cloud_coverage_threshold: int = 30) -> bool:
        """
        Check if current weather is sunny.

        Args:
            cloud_coverage_threshold: Maximum cloud coverage % to consider sunny

        Returns:
            True if sunny, False otherwise
        """
        try:
            weather_data = self.get_current_weather()

            # Check cloud coverage percentage
            clouds = weather_data.get("clouds", {}).get("all", 100)

            # Check weather condition code
            # https://openweathermap.org/weather-conditions
            weather_id = weather_data.get("weather", [{}])[0].get("id", 0)

            # Weather codes: 800 = clear, 801-804 = clouds
            # Consider sunny if clear or few clouds and below threshold
            is_clear = weather_id == 800
            is_few_clouds = 801 <= weather_id <= 802 and clouds < cloud_coverage_threshold

            return is_clear or is_few_clouds

        except (requests.RequestException, KeyError, IndexError):
            # On error, assume not sunny (conservative approach)
            return False

    def get_cloud_coverage(self) -> Optional[int]:
        """
        Get current cloud coverage percentage.

        Returns:
            Cloud coverage in percent (0-100) or None on error
        """
        try:
            weather_data = self.get_current_weather()
            return weather_data.get("clouds", {}).get("all")
        except (requests.RequestException, KeyError):
            return None

    def get_condition(self) -> WeatherCondition:
        """
        Get current weather condition category.

        Returns:
            WeatherCondition enum value
        """
        try:
            weather_data = self.get_current_weather()
            weather_id = weather_data.get("weather", [{}])[0].get("id", 0)

            # Categorize based on OpenWeatherMap weather codes
            if weather_id == 800:
                return WeatherCondition.CLEAR
            elif 801 <= weather_id <= 804:
                return WeatherCondition.CLOUDY
            elif 500 <= weather_id <= 531:
                return WeatherCondition.RAIN
            elif 600 <= weather_id <= 622:
                return WeatherCondition.SNOW
            else:
                return WeatherCondition.UNKNOWN

        except (requests.RequestException, KeyError, IndexError):
            return WeatherCondition.UNKNOWN

    def should_wait_for_sun(self, max_clouds: int = 40) -> bool:
        """
        Determine if we should wait for sun instead of forcing heating.

        Args:
            max_clouds: Maximum cloud coverage to wait for sun

        Returns:
            True if conditions suggest waiting for sun, False if should heat now
        """
        try:
            # If it's already sunny, definitely wait
            if self.is_sunny(max_clouds):
                return True

            # If cloud coverage is moderate and clearing, might be worth waiting
            clouds = self.get_cloud_coverage()
            if clouds is not None and clouds < max_clouds:
                return True

            # Otherwise, probably should heat now
            return False

        except Exception:
            # On error, conservative approach: don't wait, heat if needed
            return False

    def __repr__(self) -> str:
        """String representation."""
        if self.location_id:
            return f"WeatherService(location_id={self.location_id})"
        else:
            return f"WeatherService(lat={self.lat}, lon={self.lon})"


class MockWeatherService(WeatherService):
    """Mock weather service for testing."""

    def __init__(self, is_sunny_value: bool = False, cloud_coverage: int = 50):
        """
        Initialize mock weather service.

        Args:
            is_sunny_value: Whether to report sunny conditions
            cloud_coverage: Cloud coverage percentage
        """
        super().__init__(api_key="mock_key", location_id=0)
        self._is_sunny = is_sunny_value
        self._cloud_coverage = cloud_coverage

    def is_sunny(self, cloud_coverage_threshold: int = 30) -> bool:
        """Return mock sunny status."""
        return self._is_sunny

    def get_cloud_coverage(self) -> Optional[int]:
        """Return mock cloud coverage."""
        return self._cloud_coverage

    def set_sunny(self, is_sunny: bool) -> None:
        """Set mock sunny status."""
        self._is_sunny = is_sunny

    def set_cloud_coverage(self, coverage: int) -> None:
        """Set mock cloud coverage."""
        self._cloud_coverage = coverage
