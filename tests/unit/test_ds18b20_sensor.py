"""Tests for DS18B20 temperature sensor."""

import pytest
from pathlib import Path
from overmind.sensors.temperature import DS18B20Sensor, MockTemperatureSensor


class TestDS18B20Sensor:
    """Test DS18B20Sensor class."""

    def test_initialization(self):
        """Test sensor initialization."""
        sensor = DS18B20Sensor("28-0000072f8b4a")
        assert sensor.sensor_id == "28-0000072f8b4a"
        assert "28-0000072f8b4a" in str(sensor.device_file)

    def test_read_temperature(self, mock_ds18b20_sensor):
        """Test reading temperature from sensor."""
        sensor = DS18B20Sensor("28-0000072f8b4a", base_path=mock_ds18b20_sensor)
        temp = sensor.read_temperature()
        assert temp is not None
        assert abs(temp - 22.625) < 0.01

    def test_read_temperature_invalid_crc(self, tmp_path):
        """Test reading when CRC is invalid."""
        sensor_dir = tmp_path / "28-invalid"
        sensor_dir.mkdir(parents=True)
        sensor_file = sensor_dir / "w1_slave"
        sensor_file.write_text("6d 01 4b 46 7f ff 0c 10 3c : crc=3c NO\n"
                               "6d 01 4b 46 7f ff 0c 10 3c t=22625\n")

        sensor = DS18B20Sensor("28-invalid", base_path=str(tmp_path))
        temp = sensor.read_temperature()
        assert temp is None

    def test_sensor_not_found(self, tmp_path):
        """Test error when sensor device doesn't exist."""
        sensor = DS18B20Sensor("28-nonexistent", base_path=str(tmp_path))

        with pytest.raises(FileNotFoundError):
            sensor.read_temperature()


class TestMockTemperatureSensor:
    """Test MockTemperatureSensor class."""

    def test_mock_sensor(self):
        """Test mock sensor returns set temperature."""
        sensor = MockTemperatureSensor(temperature=25.5)
        assert sensor.read_temperature() == 25.5

    def test_set_temperature(self):
        """Test changing mock temperature."""
        sensor = MockTemperatureSensor(temperature=20.0)
        assert sensor.read_temperature() == 20.0

        sensor.set_temperature(30.0)
        assert sensor.read_temperature() == 30.0
