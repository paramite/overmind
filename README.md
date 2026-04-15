# Overmind

Solar water temperature regulation system for Wattrouter on Raspberry Pi.

## Overview

Overmind is a Python application designed to regulate water temperature in solar power plant infrastructure using the [Wattrouter](https://solarcontrols.cz/cz/wattrouter.html) device. It runs on Raspberry Pi 2B and provides intelligent temperature control based on external temperature sensors and weather conditions.

## How It Works

1. **Temperature Measurement**: Reads water temperature from a DS18B20 sensor connected to Raspberry Pi GPIO (not from Wattrouter)
2. **Weather-Aware Control**: Checks current weather conditions online via OpenWeatherMap API
3. **Intelligent Decision**: If temperature drops below threshold:
   - **Sunny weather**: Waits for sun to naturally heat the water
   - **Cloudy weather**: Enables Wattrouter to route solar power to the water heater
4. **Wattrouter Control**: Modifies Wattrouter output priority to enable/disable heating

This approach optimizes energy usage by avoiding forced heating when natural solar radiation is sufficient.

## Features

- **External Temperature Sensing**: DS18B20 1-Wire sensor via Raspberry Pi GPIO
- **Weather-Aware Control**: Integrates with OpenWeatherMap to avoid unnecessary heating
- **Wattrouter Integration**: Controls heating by modifying output configuration
- **Hysteresis Control**: Prevents rapid on/off switching
- **Configuration Management**: YAML-based configuration with environment variable overrides
- **CLI Interface**: Command-line tools for monitoring and control
- **Extensible Architecture**: Modular design for easy feature additions

## Requirements

### Hardware
- Raspberry Pi 2B (or newer) with GPIO access
- DS18B20 temperature sensor connected to GPIO (1-Wire interface)
- Wattrouter device connected to local network
- Solar power plant with water heating capability

### Software
- Python 3.8 or newer
- pip (Python package manager)
- 1-Wire kernel modules enabled on Raspberry Pi (`w1-gpio`, `w1-therm`)

## Installation

### Standard Installation

```bash
# Clone or navigate to the repository
cd /path/to/overmind

# Create virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install the package
pip install -e .
```

### Development Installation

For development with testing and linting tools:

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Install Raspberry Pi specific dependencies (only on RPi)
pip install -e ".[rpi]"
```

## Configuration

Create a configuration file at one of these locations:
- `./overmind.conf` (current directory)
- `/etc/overmind/overmind.conf` (system-wide)
- `~/.config/overmind/overmind.conf` (user-specific)

Example configuration:

```yaml
---

weather:
  api_key: your_openweathermap_api_key
  location:
    id: 3070720
    name: Mikulov
    coord:
      lon: 16.6378
      lat: 48.805561

wattrouter:
  url: http://192.168.1.100
  username: admin
  password: your_password
  output_id: O5  # Bojler (boiler) output

temperature:
  sensor_id: 28-0000072f8b4a  # Your DS18B20 sensor ID
  gpio_path: /sys/bus/w1/devices

controller:
  target_temperature: 45.0
  hysteresis: 2.0
  control_interval: 60
  weather_enabled: true
  max_cloud_coverage: 40
```

### Enabling 1-Wire on Raspberry Pi

Add to `/boot/config.txt`:
```
dtoverlay=w1-gpio
```

Then reboot and verify:
```bash
sudo modprobe w1-gpio
sudo modprobe w1-therm
ls /sys/bus/w1/devices/
```

You should see your DS18B20 sensor ID (starts with `28-`).

### Environment Variables

You can override configuration values using environment variables:

- `OVERMIND_CONFIG`: Path to configuration file
- `WEATHER_API_KEY`: Weather API key
- `WATTROUTER_URL`: Wattrouter device URL
- `WATTROUTER_USERNAME`: Wattrouter username
- `WATTROUTER_PASSWORD`: Wattrouter password

## Usage

### Check Configuration

```bash
overmind --check-config
```

### Run Temperature Controller

```bash
# Run with default 60-second interval
overmind run

# Run with custom interval
overmind run --interval 30

# Use custom configuration file
overmind -c /path/to/config.conf run
```

### Monitor Temperatures

```bash
# Monitor with default 10-second interval
overmind monitor

# Monitor with custom interval
overmind monitor --interval 5
```

## Development

### Project Structure

```
overmind/
├── src/overmind/           # Source code
│   ├── config/            # Configuration management
│   ├── controllers/       # Temperature controllers
│   ├── sensors/           # Sensor interfaces (Wattrouter)
│   ├── utils/             # Utility functions
│   └── cli.py            # Command-line interface
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── fixtures/         # Test fixtures
├── docs/                  # Documentation
├── config/                # Configuration examples
└── pyproject.toml        # Project metadata and dependencies
```

### Running Tests

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit

# Run with coverage report
pytest --cov=overmind --cov-report=html

# Run specific test markers
pytest -m unit
pytest -m integration
pytest -m "not rpi"  # Skip Raspberry Pi hardware tests
```

### Code Quality

```bash
# Format code
black src tests

# Sort imports
isort src tests

# Lint code
flake8 src tests

# Type checking
mypy src

# Run all pre-commit hooks
pre-commit run --all-files
```

### Building

```bash
# Build distribution packages
pip install build
python -m build

# Install locally from build
pip install dist/overmind-*.whl
```

## Architecture

### Components

1. **Configuration Layer** (`overmind.config`)
   - Settings management with YAML and environment variables
   - Centralized configuration access

2. **Sensor Layer** (`overmind.sensors`)
   - **DS18B20 Temperature Sensor**: Reads water temperature via Raspberry Pi GPIO
   - **Wattrouter Client**: Controls heating by modifying output configuration
   - **Weather Service**: Fetches current weather from OpenWeatherMap API
   - Extensible for additional sensor types

3. **Controller Layer** (`overmind.controllers`)
   - Weather-aware temperature regulation
   - Hysteresis control prevents rapid switching
   - Intelligent decision making (heat now vs. wait for sun)

4. **CLI Layer** (`overmind.cli`)
   - Command-line interface for all operations
   - Monitoring and control commands

### Control Algorithm

The temperature controller uses a weather-aware hysteresis-based algorithm:

1. **Temperature above target + hysteresis/2**: Disable heating (water is warm enough)

2. **Temperature below target - hysteresis/2**:
   - **If sunny** (cloud coverage < threshold): Wait for sun, don't heat
   - **If cloudy**: Enable heating via Wattrouter

3. **Temperature within hysteresis band**: Maintain current state

This approach:
- Prevents rapid on/off switching (extends equipment lifetime)
- Optimizes energy usage (waits for free solar radiation when possible)
- Only forces heating when necessary (cloudy weather + low temperature)

**Example** (target=45°C, hysteresis=2°C, max_clouds=40%):
- Temp=43°C, clouds=20% → Wait for sun (sunny)
- Temp=43°C, clouds=80% → Enable heating (cloudy)
- Temp=46.5°C → Disable heating (target reached)
- Temp=44.5°C → Keep current state (within band)

## Raspberry Pi Deployment

### System Service

Create `/etc/systemd/system/overmind.service`:

```ini
[Unit]
Description=Overmind Temperature Controller
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/overmind
Environment="PATH=/home/pi/overmind/.venv/bin"
ExecStart=/home/pi/overmind/.venv/bin/overmind run
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable overmind
sudo systemctl start overmind
sudo systemctl status overmind
```

### Monitoring

View logs:

```bash
# Follow logs
sudo journalctl -u overmind -f

# View recent logs
sudo journalctl -u overmind -n 100
```

## Troubleshooting

### Cannot connect to Wattrouter

1. Check network connectivity: `ping <wattrouter_ip>`
2. Verify Wattrouter URL in configuration
3. Check credentials (username/password)
4. Ensure Wattrouter web interface is accessible

### Temperature sensor not found

1. Check 1-Wire modules are loaded:
   ```bash
   lsmod | grep w1
   ```
2. Verify sensor connection to GPIO
3. Check sensor ID:
   ```bash
   ls /sys/bus/w1/devices/
   cat /sys/bus/w1/devices/28-*/w1_slave
   ```
4. Update `sensor_id` in configuration

### Temperature readings are incorrect

1. Verify DS18B20 sensor is working:
   ```bash
   cat /sys/bus/w1/devices/28-YOUR_SENSOR_ID/w1_slave
   ```
2. Check for CRC errors (first line should end with "YES")
3. Temperature is in format `t=XXXXX` (value in millidegrees)

### Controller not regulating properly

1. Check target temperature and hysteresis settings
2. Verify control interval is appropriate
3. Review logs for errors
4. Test controller logic with monitor command first

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Run code quality tools
7. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Check documentation in `docs/`
- Review existing issues
- Create new issue with detailed description

## Related Projects

- [Wattrouter](https://solarcontrols.cz/cz/wattrouter.html) - Solar power routing device
- [OpenStack Telemetry](https://docs.openstack.org/telemetry/) - Monitoring and metering

## Acknowledgments

- Wattrouter by Solar Controls
- Built for deployment on Raspberry Pi
