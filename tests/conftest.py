"""Pytest configuration and shared fixtures."""

import pytest
from pathlib import Path


@pytest.fixture
def test_config_path(tmp_path):
    """Create a temporary configuration file for testing."""
    config_content = """---

weather:
  api_key: test_api_key
  location:
    id: 3070720
    name: Mikulov
    coord:
      lon: 16.6378
      lat: 48.805561

wattrouter:
  url: http://192.168.1.100
  username: admin
  password: test_password
  output_id: O5

temperature:
  sensor_id: 28-0000072f8b4a
  gpio_path: /sys/bus/w1/devices

controller:
  target_temperature: 45.0
  hysteresis: 2.0
  control_interval: 60
  weather_enabled: true
  max_cloud_coverage: 40
"""
    config_file = tmp_path / "test_overmind.conf"
    config_file.write_text(config_content)
    return config_file


@pytest.fixture
def fixtures_path():
    """Get path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def wattrouter_meas_xml(fixtures_path):
    """Load real Wattrouter measurement XML."""
    meas_file = fixtures_path / "meas.xml"
    if meas_file.exists():
        return meas_file.read_text()
    # Fallback minimal XML
    return """<?xml version="1.0"?>
<meas>
  <O5>
    <A>0</A>
    <P>0.00</P>
    <E>1.85</E>
  </O5>
  <PPS>-1.61</PPS>
</meas>
"""


@pytest.fixture
def wattrouter_conf_get_xml(fixtures_path):
    """Load real Wattrouter configuration XML."""
    conf_file = fixtures_path / "conf_get.xml"
    if conf_file.exists():
        return conf_file.read_text()
    # Fallback minimal XML
    return """<?xml version="1.0"?>
<conf>
  <O5>
    <N>Bojler</N>
    <F>1</F>
    <Pr>1</Pr>
    <Ph>0</Ph>
    <M>0</M>
  </O5>
</conf>
"""


@pytest.fixture
def mock_ds18b20_sensor(tmp_path):
    """Create mock DS18B20 sensor file."""
    sensor_dir = tmp_path / "28-0000072f8b4a"
    sensor_dir.mkdir(parents=True)
    sensor_file = sensor_dir / "w1_slave"
    sensor_file.write_text("6d 01 4b 46 7f ff 0c 10 3c : crc=3c YES\n"
                           "6d 01 4b 46 7f ff 0c 10 3c t=22625\n")
    return str(tmp_path)
