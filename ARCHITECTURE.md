# Overmind Architecture

## System Overview

Overmind is a weather-aware water temperature regulation system for solar power plants using Wattrouter.

```
┌─────────────────┐
│  Raspberry Pi   │
│                 │
│  ┌───────────┐  │
│  │ DS18B20   │  │  External temperature sensor
│  │  Sensor   │  │  (GPIO 1-Wire)
│  └─────┬─────┘  │
│        │        │
│  ┌─────▼─────┐  │
│  │ Overmind  │  │  Main control application
│  │ Controller│  │
│  └─────┬─────┘  │
│        │        │
└────────┼────────┘
         │
    ┌────┴────┬──────────────┐
    │         │              │
    ▼         ▼              ▼
┌────────┐ ┌──────────┐ ┌──────────┐
│ Wattro-│ │OpenWeather│ │  User    │
│ uter   │ │  API     │ │  CLI     │
│        │ │          │ │          │
│ Control│ │ Weather  │ │ Monitor  │
│ Heating│ │ Data     │ │ & Config │
└────────┘ └──────────┘ └──────────┘
```

## Control Flow

1. **Read Temperature**: DS18B20 sensor via GPIO → Current water temperature
2. **Check Weather**: OpenWeatherMap API → Is it sunny?
3. **Decision Logic**:
   ```
   if temperature > target + hysteresis/2:
       disable_heating()  # Water is warm enough
   
   elif temperature < target - hysteresis/2:
       if is_sunny() and weather_enabled:
           disable_heating()  # Wait for sun
       else:
           enable_heating()   # Force heating (cloudy)
   
   else:
       maintain_current_state()  # Within hysteresis band
   ```
4. **Control Wattrouter**: Modify output priority via HTTP API

## Component Architecture

### 1. Sensors Layer (`overmind.sensors`)

#### DS18B20 Temperature Sensor
- **Purpose**: Read water temperature from external sensor
- **Interface**: 1-Wire protocol via `/sys/bus/w1/devices/`
- **Output**: Temperature in Celsius
- **Hardware**: Connected to Raspberry Pi GPIO

#### Weather Service
- **Purpose**: Fetch current weather conditions
- **API**: OpenWeatherMap API
- **Methods**:
  - `is_sunny()` - Check if conditions are sunny
  - `get_cloud_coverage()` - Get cloud percentage
  - `should_wait_for_sun()` - Decision helper
- **Logic**: Weather ID codes + cloud coverage analysis

#### Wattrouter Client
- **Purpose**: Control heating via Wattrouter device
- **Protocol**: HTTP/XML API
- **Methods**:
  - `get_configuration()` - Read current config
  - `enable_heating()` - Set output priority to enable
  - `disable_heating()` - Set output priority to disable
  - `is_heating_enabled()` - Check current state
- **Output**: Default O5 (Bojler/Boiler)

### 2. Controller Layer (`overmind.controllers`)

#### Temperature Controller
- **Algorithm**: Hysteresis-based control with weather awareness
- **Inputs**:
  - Current temperature (from sensor)
  - Weather conditions (from API)
  - Target temperature (from config)
- **Output**: Heating on/off decision
- **Features**:
  - Prevents oscillation (hysteresis)
  - Energy optimization (weather-aware)
  - Configurable thresholds

### 3. Configuration Layer (`overmind.config`)

#### Settings Management
- **Format**: YAML configuration file
- **Override**: Environment variables take precedence
- **Locations** (in order):
  1. Path specified via `--config`
  2. `$OVERMIND_CONFIG` environment variable
  3. `./overmind.conf`
  4. `/etc/overmind/overmind.conf`
  5. `~/.config/overmind/overmind.conf`

### 4. CLI Layer (`overmind.cli`)

#### Commands
- `overmind run` - Start main control loop
- `overmind monitor` - Display current status
- `overmind --check-config` - Validate configuration

## Data Flow

```
┌─────────────────────────────────────────────────────────┐
│                    Main Control Loop                    │
│                                                         │
│  1. Read temperature from DS18B20                      │
│     └─> temp = sensor.read_temperature()               │
│                                                         │
│  2. Check weather conditions                           │
│     └─> is_sunny = weather.is_sunny()                  │
│                                                         │
│  3. Calculate control signal                           │
│     └─> should_heat = controller.should_heat(temp,     │
│                                            is_sunny)    │
│                                                         │
│  4. Update Wattrouter if state changed                 │
│     └─> if should_heat:                                │
│             wattrouter.enable_heating()                │
│         else:                                          │
│             wattrouter.disable_heating()               │
│                                                         │
│  5. Wait for control_interval                          │
│     └─> sleep(60)                                      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Configuration Schema

```yaml
weather:
  api_key: string          # OpenWeatherMap API key
  location:
    id: integer            # City ID
    name: string           # City name (informational)
    coord:
      lat: float           # Latitude
      lon: float           # Longitude

wattrouter:
  url: string              # Device URL (http://...)
  username: string         # HTTP auth username
  password: string         # HTTP auth password
  output_id: string        # Output controlling heater (e.g., O5)

temperature:
  sensor_id: string        # DS18B20 sensor ID (28-...)
  gpio_path: string        # Base path for 1-Wire devices

controller:
  target_temperature: float     # Target in °C
  hysteresis: float             # Hysteresis band in °C
  control_interval: integer     # Loop interval in seconds
  weather_enabled: boolean      # Enable weather awareness
  max_cloud_coverage: integer   # Max clouds % for "sunny"
```

## Decision Matrix

| Temperature | Weather | Weather Enabled | Action |
|-------------|---------|-----------------|--------|
| > target + hyst/2 | Any | Any | **OFF** (water warm) |
| < target - hyst/2 | Sunny | Yes | **OFF** (wait for sun) |
| < target - hyst/2 | Cloudy | Yes | **ON** (force heating) |
| < target - hyst/2 | Any | No | **ON** (weather ignored) |
| Within band | Any | Any | **MAINTAIN** (no change) |

## Error Handling

### Sensor Failures
- **DS18B20 read error**: Log warning, keep previous state
- **CRC check failed**: Retry read, log if persistent
- **Sensor not found**: Raise error, cannot operate

### API Failures
- **Weather API timeout**: Assume not sunny (conservative)
- **Wattrouter unreachable**: Log error, retry on next cycle
- **Configuration POST failed**: Log error, retry

### Safety
- **Maximum temperature limit**: Force disable if exceeded
- **Minimum temperature limit**: Force enable for frost protection
- **Persistent failures**: Alert via notifications (if configured)

## Testing Strategy

### Unit Tests
- Mock external dependencies (GPIO, HTTP APIs)
- Test control logic in isolation
- Verify configuration parsing
- Test hysteresis behavior

### Integration Tests
- Test with mock sensors and devices
- Verify end-to-end control flow
- Test error recovery

### Hardware Tests (Raspberry Pi required)
- Marked with `@pytest.mark.rpi`
- Skipped in CI/development
- Test actual GPIO sensor reading

## Deployment Architecture

### Systemd Service
```
/etc/systemd/system/overmind.service
├─> Runs overmind run command
├─> Auto-restart on failure
├─> Logs to journald
└─> Starts after network.target
```

### File Locations
```
/home/pi/overmind/               # Installation directory
├── .venv/                       # Virtual environment
├── src/                         # Source code
└── overmind.conf                # Local config

/etc/overmind/                   # System config
└── overmind.conf                # System-wide config

/var/log/overmind/               # Logs (if file logging enabled)
└── overmind.log

/sys/bus/w1/devices/             # 1-Wire sensors
└── 28-XXXXXXXXXXXX/             # DS18B20 sensor
    └── w1_slave                 # Temperature reading
```

## Performance Considerations

- **Control Loop**: 60-second default interval (configurable)
- **API Calls**: 
  - Weather: 1 per control cycle (within free tier limits)
  - Wattrouter: Only when state changes (minimize writes)
- **GPIO Read**: Fast (< 1 second) but may retry on CRC error
- **Memory**: Minimal (~20MB Python process)
- **CPU**: Negligible (mostly sleeping)

## Future Extensions

Possible enhancements:
- Multiple temperature sensors (differential control)
- Time-based schedules (different targets by time of day)
- Historical data logging (InfluxDB, Prometheus)
- Web dashboard (Flask/FastAPI)
- Machine learning for weather prediction
- SMS/Push notifications
- Integration with home automation (Home Assistant)
