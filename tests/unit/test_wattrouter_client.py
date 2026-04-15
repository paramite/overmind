"""Tests for Wattrouter client."""

import pytest
import requests
from unittest.mock import Mock, patch
from overmind.sensors.wattrouter import WattrouterClient


class TestWattrouterClient:
    """Test WattrouterClient class."""

    def test_initialization(self):
        """Test client initialization."""
        client = WattrouterClient("http://192.168.1.1", "admin", "password", "O5")
        assert client.base_url == "http://192.168.1.1"
        assert client.username == "admin"
        assert client.password == "password"
        assert client.output_id == "O5"

    def test_base_url_trailing_slash_removed(self):
        """Test that trailing slash is removed from base URL."""
        client = WattrouterClient("http://192.168.1.1/", "admin", "password")
        assert client.base_url == "http://192.168.1.1"

    @patch('requests.Session.get')
    def test_get_measurements(self, mock_get, wattrouter_meas_xml):
        """Test fetching measurements from Wattrouter."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = wattrouter_meas_xml
        mock_get.return_value = mock_response

        client = WattrouterClient("http://192.168.1.1")
        measurements = client.get_measurements()

        # Verify we got some measurements back
        assert measurements is not None
        assert isinstance(measurements, dict)
        mock_get.assert_called_once()

    @patch('requests.Session.get')
    def test_is_heating_enabled(self, mock_get, wattrouter_conf_get_xml):
        """Test checking if heating is enabled."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = wattrouter_conf_get_xml
        mock_get.return_value = mock_response

        client = WattrouterClient("http://192.168.1.1", output_id="O5")
        is_enabled = client.is_heating_enabled()

        # Based on conf_get.xml, O5 (Bojler) has Pr=1, so it's enabled
        assert is_enabled is True

    @patch('requests.Session.post')
    def test_enable_heating(self, mock_post):
        """Test enabling heating."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        client = WattrouterClient("http://192.168.1.1", output_id="O5")
        result = client.enable_heating()

        assert result is True
        mock_post.assert_called_once()

    @patch('requests.Session.post')
    def test_disable_heating(self, mock_post):
        """Test disabling heating."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        client = WattrouterClient("http://192.168.1.1", output_id="O5")
        result = client.disable_heating()

        assert result is True
        mock_post.assert_called_once()

    @patch('requests.Session.get')
    def test_get_configuration(self, mock_get, wattrouter_conf_get_xml):
        """Test fetching configuration from Wattrouter."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = wattrouter_conf_get_xml
        mock_get.return_value = mock_response

        client = WattrouterClient("http://192.168.1.1")
        config = client.get_configuration()

        assert config is not None
        assert isinstance(config, dict)

    @patch('requests.Session.post')
    def test_set_configuration(self, mock_post):
        """Test setting Wattrouter configuration."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        client = WattrouterClient("http://192.168.1.1")
        result = client.set_configuration({"target_temp": 50.0})

        assert result is True
        mock_post.assert_called_once()

    @patch('requests.Session.get')
    def test_request_timeout(self, mock_get):
        """Test that requests have timeout set."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<meas><T1>42.5</T1></meas>"
        mock_get.return_value = mock_response

        client = WattrouterClient("http://192.168.1.1")
        client.get_measurements()

        # Verify timeout was passed
        call_kwargs = mock_get.call_args[1]
        assert "timeout" in call_kwargs
        assert call_kwargs["timeout"] == 10

    def test_context_manager(self):
        """Test using client as context manager."""
        with WattrouterClient("http://192.168.1.1") as client:
            assert client is not None
            assert isinstance(client, WattrouterClient)
