# Overmind Quick Start Guide

## Installation

```bash
cd /Users/para/Work/side/overmind

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# For Raspberry Pi, also install GPIO dependencies
pip install -e ".[rpi]"
```

## Configuration

1. **Copy example config:**
   ```bash
   cp config/overmind.conf.example overmind.conf
   ```

2. **Edit overmind.conf:**
   ```yaml
   weather:
     api_key: YOUR_OPENWEATHERMAP_API_KEY  # Get from openweathermap.org
   
   wattrouter:
     url: http://192.168.1.100  # Your Wattrouter IP
     password: your_password
   
   temperature:
     sensor_id: 28-0000072f8b4a  # Your DS18B20 ID (see below)
   
   controller:
     target_temperature: 45.0
     hysteresis: 2.0
   ```

3. **Find your DS18B20 sensor ID:**
   ```bash
   ls /sys/bus/w1/devices/
   # Look for ID starting with 28-
   ```

## Testing

```bash
# Run all tests
make test

# Run only unit tests (no hardware needed)
make test-unit

# Run tests with coverage
make coverage

# Run linters
make lint

# Format code
make format
```

## Running

```bash
# Check configuration
overmind --check-config

# Monitor temperatures (read-only)
overmind monitor

# Start controller (controls heating)
overmind run

# Use custom config
overmind -c /path/to/config.conf run
```

## Development Workflow

```bash
# Install pre-commit hooks
pre-commit install

# Make code changes
# ...

# Run tests
make test

# Check formatting
make format-check

# Fix formatting
make format

# Run linters
make lint
```

## Raspberry Pi Setup

1. **Enable 1-Wire:**
   ```bash
   # Add to /boot/config.txt
   echo "dtoverlay=w1-gpio" | sudo tee -a /boot/config.txt
   
   # Reboot
   sudo reboot
   
   # After reboot, load modules
   sudo modprobe w1-gpio
   sudo modprobe w1-therm
   ```

2. **Connect DS18B20:**
   - Data pin → GPIO 4 (Pin 7)
   - VCC → 3.3V (Pin 1)
   - GND → Ground (Pin 6)
   - 4.7kΩ resistor between Data and VCC

3. **Verify sensor:**
   ```bash
   ls /sys/bus/w1/devices/
   cat /sys/bus/w1/devices/28-*/w1_slave
   ```

4. **Install as systemd service:**
   ```bash
   sudo cp overmind.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable overmind
   sudo systemctl start overmind
   sudo systemctl status overmind
   ```

## Troubleshooting

### Sensor Not Found
```bash
# Check modules
lsmod | grep w1

# Load manually if needed
sudo modprobe w1-gpio
sudo modprobe w1-therm

# Check devices
ls -l /sys/bus/w1/devices/
```

### Wattrouter Connection Issues
```bash
# Test connectivity
ping YOUR_WATTROUTER_IP

# Test HTTP access
curl http://YOUR_WATTROUTER_IP/meas.xml

# With authentication
curl -u admin:password http://YOUR_WATTROUTER_IP/conf_get.xml
```

### Weather API Issues
```bash
# Test API key
curl "https://api.openweathermap.org/data/2.5/weather?id=3070720&appid=YOUR_API_KEY"
```

## Project Structure

```
overmind/
├── src/overmind/           # Source code
│   ├── config/            # Configuration management
│   ├── controllers/       # Temperature control logic
│   ├── sensors/           # Sensor interfaces
│   │   ├── temperature.py # DS18B20 GPIO sensor
│   │   ├── wattrouter.py  # Wattrouter client
│   │   └── weather.py     # Weather service
│   └── cli.py             # Command-line interface
├── tests/                 # Test suite
│   ├── fixtures/          # Test data (XML files)
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
├── config/                # Configuration examples
├── pyproject.toml         # Project metadata
├── Makefile               # Common tasks
└── README.md              # Full documentation
```

## Next Steps

1. **Read ARCHITECTURE.md** for detailed system design
2. **Review tests/** for usage examples
3. **Check existing XML files** in tests/fixtures/ to understand Wattrouter format
4. **Customize controller settings** for your specific needs

## Common Commands Reference

```bash
# Development
make install-dev          # Install with dev dependencies
make test                 # Run all tests
make coverage             # Generate coverage report
make lint                 # Run linters
make format               # Format code

# Running
overmind --check-config   # Validate configuration
overmind run              # Start controller
overmind monitor          # Monitor only

# Cleanup
make clean                # Remove build artifacts
```

## Environment Variables

```bash
# Override config file location
export OVERMIND_CONFIG=/path/to/overmind.conf

# Override API keys (more secure than storing in file)
export WEATHER_API_KEY=your_key_here
export WATTROUTER_PASSWORD=your_password_here
```

## Integration with Existing notify_high_rate.py

The existing `scripts/notify_high_rate.py` can work alongside Overmind:
- Overmind: Controls heating based on temperature + weather
- notify_high_rate.py: Sends notifications for high power consumption

Both can read from the same Wattrouter device independently.
