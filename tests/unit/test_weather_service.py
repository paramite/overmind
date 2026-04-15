"""Tests for weather service."""

import pytest
from unittest.mock import Mock, patch
from overmind.sensors.weather import WeatherService, WeatherCondition, MockWeatherService


class TestWeatherService:
    """Test WeatherService class."""

    def test_initialization_with_location_id(self):
        """Test initializing with location ID."""
        service = WeatherService(api_key="test_key", location_id=3070720)
        assert service.api_key == "test_key"
        assert service.location_id == 3070720

    def test_initialization_with_coordinates(self):
        """Test initializing with lat/lon."""
        service = WeatherService(api_key="test_key", lat=48.8, lon=16.6)
        assert service.api_key == "test_key"
        assert service.lat == 48.8
        assert service.lon == 16.6

    @patch('requests.get')
    def test_get_current_weather_by_id(self, mock_get):
        """Test fetching weather by location ID."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "weather": [{"id": 800, "main": "Clear"}],
            "clouds": {"all": 10},
            "main": {"temp": 25.5}
        }
        mock_get.return_value = mock_response

        service = WeatherService(api_key="test_key", location_id=3070720)
        weather = service.get_current_weather()

        assert weather["weather"][0]["main"] == "Clear"
        assert weather["clouds"]["all"] == 10
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_is_sunny_clear_sky(self, mock_get):
        """Test sunny detection with clear sky."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "weather": [{"id": 800}],  # Clear sky
            "clouds": {"all": 0}
        }
        mock_get.return_value = mock_response

        service = WeatherService(api_key="test_key", location_id=3070720)
        assert service.is_sunny() is True

    @patch('requests.get')
    def test_is_sunny_few_clouds(self, mock_get):
        """Test sunny detection with few clouds."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "weather": [{"id": 801}],  # Few clouds
            "clouds": {"all": 20}
        }
        mock_get.return_value = mock_response

        service = WeatherService(api_key="test_key", location_id=3070720)
        assert service.is_sunny(cloud_coverage_threshold=30) is True

    @patch('requests.get')
    def test_is_not_sunny_overcast(self, mock_get):
        """Test not sunny with overcast."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "weather": [{"id": 804}],  # Overcast
            "clouds": {"all": 90}
        }
        mock_get.return_value = mock_response

        service = WeatherService(api_key="test_key", location_id=3070720)
        assert service.is_sunny() is False

    @patch('requests.get')
    def test_get_cloud_coverage(self, mock_get):
        """Test getting cloud coverage percentage."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "weather": [{"id": 802}],
            "clouds": {"all": 45}
        }
        mock_get.return_value = mock_response

        service = WeatherService(api_key="test_key", location_id=3070720)
        coverage = service.get_cloud_coverage()

        assert coverage == 45

    @patch('requests.get')
    def test_get_condition_clear(self, mock_get):
        """Test getting clear weather condition."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "weather": [{"id": 800}],
            "clouds": {"all": 0}
        }
        mock_get.return_value = mock_response

        service = WeatherService(api_key="test_key", location_id=3070720)
        condition = service.get_condition()

        assert condition == WeatherCondition.CLEAR

    @patch('requests.get')
    def test_should_wait_for_sun_sunny(self, mock_get):
        """Test should wait when sunny."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "weather": [{"id": 800}],
            "clouds": {"all": 10}
        }
        mock_get.return_value = mock_response

        service = WeatherService(api_key="test_key", location_id=3070720)
        assert service.should_wait_for_sun() is True

    @patch('requests.get')
    def test_should_not_wait_heavy_clouds(self, mock_get):
        """Test should not wait with heavy clouds."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "weather": [{"id": 804}],
            "clouds": {"all": 90}
        }
        mock_get.return_value = mock_response

        service = WeatherService(api_key="test_key", location_id=3070720)
        assert service.should_wait_for_sun(max_clouds=40) is False


class TestMockWeatherService:
    """Test MockWeatherService class."""

    def test_mock_service_sunny(self):
        """Test mock service returns sunny."""
        service = MockWeatherService(is_sunny_value=True, cloud_coverage=20)
        assert service.is_sunny() is True
        assert service.get_cloud_coverage() == 20

    def test_mock_service_not_sunny(self):
        """Test mock service returns not sunny."""
        service = MockWeatherService(is_sunny_value=False, cloud_coverage=80)
        assert service.is_sunny() is False
        assert service.get_cloud_coverage() == 80

    def test_set_sunny(self):
        """Test changing mock sunny status."""
        service = MockWeatherService(is_sunny_value=False)
        assert service.is_sunny() is False

        service.set_sunny(True)
        assert service.is_sunny() is True

    def test_set_cloud_coverage(self):
        """Test changing mock cloud coverage."""
        service = MockWeatherService(cloud_coverage=50)
        assert service.get_cloud_coverage() == 50

        service.set_cloud_coverage(25)
        assert service.get_cloud_coverage() == 25
