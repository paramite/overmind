"""Tests for temperature controller."""

import pytest
from overmind.controllers.temperature import TemperatureController


class TestTemperatureController:
    """Test TemperatureController class."""

    def test_initialization(self):
        """Test controller initialization."""
        controller = TemperatureController(target_temp=45.0, hysteresis=2.0)
        assert controller.target_temp == 45.0
        assert controller.hysteresis == 2.0
        assert controller.weather_enabled is True
        assert controller.state is False

    def test_heating_below_target_cloudy(self):
        """Test heating enabled when temp below target and cloudy."""
        controller = TemperatureController(target_temp=45.0, hysteresis=2.0)

        # Temperature well below target, not sunny
        signal = controller.should_heat(40.0, is_sunny=False)
        assert signal is True
        assert controller.state is True

    def test_no_heating_below_target_sunny(self):
        """Test heating disabled when temp below target but sunny."""
        controller = TemperatureController(target_temp=45.0, hysteresis=2.0)

        # Temperature below target, but sunny - wait for sun
        signal = controller.should_heat(40.0, is_sunny=True)
        assert signal is False
        assert controller.state is False

    def test_heating_below_target_sunny_weather_disabled(self):
        """Test heating enabled when sunny but weather control disabled."""
        controller = TemperatureController(target_temp=45.0, hysteresis=2.0,
                                           weather_enabled=False)

        # Temperature below target, sunny, but weather control off
        signal = controller.should_heat(40.0, is_sunny=True)
        assert signal is True
        assert controller.state is True

    def test_no_heating_above_target(self):
        """Test heating disabled when temperature above target."""
        controller = TemperatureController(target_temp=45.0, hysteresis=2.0)

        # First enable heating
        controller.should_heat(40.0, is_sunny=False)

        # Temperature well above target
        signal = controller.should_heat(48.0, is_sunny=False)
        assert signal is False
        assert controller.state is False

    def test_hysteresis_prevents_oscillation(self):
        """Test that hysteresis prevents rapid switching."""
        controller = TemperatureController(target_temp=45.0, hysteresis=2.0)

        # Start with heating off, temp slightly below target
        controller._current_state = False
        signal = controller.should_heat(44.5, is_sunny=False)
        # Should remain off due to hysteresis (44.5 > 45 - 2/2 = 44)
        assert signal is False

        # Drop below lower threshold, not sunny
        signal = controller.should_heat(43.5, is_sunny=False)
        assert signal is True

        # Rise slightly but stay within hysteresis band
        signal = controller.should_heat(44.5, is_sunny=False)
        # Should remain on (44.5 < 45 + 2/2 = 46)
        assert signal is True

        # Rise above upper threshold
        signal = controller.should_heat(46.5, is_sunny=False)
        assert signal is False

    def test_sunny_overrides_heating_when_below_target(self):
        """Test that sunny weather prevents heating even when cold."""
        controller = TemperatureController(target_temp=45.0, hysteresis=2.0)

        # Temp is 40°C (below 44°C threshold), sunny
        signal = controller.should_heat(40.0, is_sunny=True)
        assert signal is False  # Wait for sun to heat

        # Same temp, but not sunny
        signal = controller.should_heat(40.0, is_sunny=False)
        assert signal is True  # Now should heat

    def test_set_target(self):
        """Test changing target temperature."""
        controller = TemperatureController(target_temp=45.0, hysteresis=2.0)
        controller.set_target(50.0)
        assert controller.target_temp == 50.0

    def test_enable_disable_weather_control(self):
        """Test enabling/disabling weather control."""
        controller = TemperatureController(target_temp=45.0, hysteresis=2.0)

        # Weather enabled by default
        assert controller.weather_enabled is True

        # Disable weather control
        controller.enable_weather_control(False)
        assert controller.weather_enabled is False

        # Re-enable
        controller.enable_weather_control(True)
        assert controller.weather_enabled is True

    def test_repr(self):
        """Test string representation."""
        controller = TemperatureController(target_temp=45.0, hysteresis=2.0)
        repr_str = repr(controller)
        assert "45" in repr_str
        assert "2.0" in repr_str
        assert "weather=" in repr_str
