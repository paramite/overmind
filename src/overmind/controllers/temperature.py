"""Temperature regulation controller with weather-aware logic."""

from typing import Optional


class TemperatureController:
    """
    Controls water temperature based on sensor readings, target setpoint, and weather.

    This controller maintains water temperature at a target value by enabling/disabling
    heating via Wattrouter. It considers weather conditions to avoid unnecessary heating
    when solar radiation alone can heat the water.
    """

    def __init__(self, target_temp: float, hysteresis: float = 2.0,
                 weather_enabled: bool = True, max_cloud_coverage: int = 40):
        """
        Initialize temperature controller.

        Args:
            target_temp: Target temperature in Celsius
            hysteresis: Temperature hysteresis for control logic (prevents oscillation)
            weather_enabled: Whether to consider weather in control decisions
            max_cloud_coverage: Maximum cloud coverage % to wait for sun
        """
        self.target_temp = target_temp
        self.hysteresis = hysteresis
        self.weather_enabled = weather_enabled
        self.max_cloud_coverage = max_cloud_coverage
        self._current_state: bool = False

    def should_heat(self, current_temp: float, is_sunny: bool = False) -> bool:
        """
        Determine if heating should be enabled.

        Decision logic:
        1. If temp is above target + hysteresis/2: disable heating
        2. If temp is below target - hysteresis/2:
           a. If sunny and weather_enabled: wait for sun (no heating)
           b. Otherwise: enable heating
        3. If temp is within hysteresis band: maintain current state

        Args:
            current_temp: Current measured temperature in Celsius
            is_sunny: Whether current weather is sunny

        Returns:
            True if heating should be enabled, False otherwise
        """
        temp_high = self.target_temp + self.hysteresis / 2
        temp_low = self.target_temp - self.hysteresis / 2

        # Above target: definitely turn off heating
        if current_temp > temp_high:
            self._current_state = False

        # Below target: check if we should heat
        elif current_temp < temp_low:
            # If sunny and weather consideration is enabled, wait for sun
            if self.weather_enabled and is_sunny:
                self._current_state = False
            else:
                # Not sunny or weather disabled: enable heating
                self._current_state = True

        # Within hysteresis band: maintain current state
        # This prevents rapid on/off switching

        return self._current_state

    @property
    def state(self) -> bool:
        """Get current control state."""
        return self._current_state

    def set_target(self, target_temp: float) -> None:
        """Set new target temperature."""
        self.target_temp = target_temp

    def enable_weather_control(self, enabled: bool = True) -> None:
        """Enable or disable weather-aware control."""
        self.weather_enabled = enabled

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"TemperatureController(target={self.target_temp}°C, "
            f"hysteresis={self.hysteresis}°C, weather={self.weather_enabled}, "
            f"state={self._current_state})"
        )
