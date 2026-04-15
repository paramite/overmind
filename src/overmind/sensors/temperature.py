"""Temperature sensor interface for Raspberry Pi GPIO."""

import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class TemperatureSensor(ABC):
    """Abstract base class for temperature sensors."""

    @abstractmethod
    def read_temperature(self) -> Optional[float]:
        """Read temperature in Celsius."""
        pass


class DS18B20Sensor(TemperatureSensor):
    """DS18B20 1-Wire temperature sensor connected via GPIO."""

    def __init__(self, sensor_id: str, base_path: str = "/sys/bus/w1/devices"):
        """
        Initialize DS18B20 sensor.

        Args:
            sensor_id: Sensor ID (e.g., '28-0000072f8b4a')
            base_path: Base path to 1-Wire devices (default: /sys/bus/w1/devices)
        """
        self.sensor_id = sensor_id
        self.device_file = Path(base_path) / sensor_id / "w1_slave"

    def read_raw(self) -> str:
        """Read raw data from sensor file."""
        if not self.device_file.exists():
            raise FileNotFoundError(f"Sensor device not found: {self.device_file}")

        with open(self.device_file, "r") as f:
            return f.read()

    def read_temperature(self) -> Optional[float]:
        """
        Read temperature from DS18B20 sensor.

        Returns:
            Temperature in Celsius or None if read failed

        Raises:
            FileNotFoundError: If sensor device file doesn't exist
        """
        try:
            lines = self.read_raw().strip().split("\n")

            # Check CRC validity (first line ends with YES)
            if len(lines) < 2 or not lines[0].strip().endswith("YES"):
                return None

            # Extract temperature from second line (format: t=XXXXX)
            temp_pos = lines[1].find("t=")
            if temp_pos == -1:
                return None

            temp_string = lines[1][temp_pos + 2:]
            temp_c = float(temp_string) / 1000.0

            return temp_c

        except (IOError, ValueError, IndexError) as e:
            return None

    def __repr__(self) -> str:
        """String representation."""
        return f"DS18B20Sensor(sensor_id={self.sensor_id})"


class MockTemperatureSensor(TemperatureSensor):
    """Mock temperature sensor for testing."""

    def __init__(self, temperature: float = 25.0):
        """
        Initialize mock sensor.

        Args:
            temperature: Temperature to return in Celsius
        """
        self._temperature = temperature

    def read_temperature(self) -> Optional[float]:
        """Read temperature from mock sensor."""
        return self._temperature

    def set_temperature(self, temperature: float) -> None:
        """Set the mock temperature value."""
        self._temperature = temperature

    def __repr__(self) -> str:
        """String representation."""
        return f"MockTemperatureSensor(temperature={self._temperature}°C)"
