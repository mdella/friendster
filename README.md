# Friendster - Modular ESP32 Application

This is a refactored, modular version of the Friendster ESP32 application. The code has been organized into separate modules based on functionality for better maintainability and reusability.

## File Structure

```
├── main.py              # Main program that ties everything together
├── constants.py         # Shared constants and configuration values
├── led_ring.py          # LED ring control and animations
├── button_handler.py    # Button input with debouncing
├── config_manager.py    # Configuration file loading/saving
├── mqtt_handler.py      # MQTT connection and messaging
├── ota_handler.py       # Over-the-air update management
├── wifi_manager.py      # WiFi connection and AP mode
└── web_server.py        # Captive portal and web configuration
```

## Module Descriptions

### constants.py
Contains all shared configuration values:
- File paths for WiFi and MQTT configurations
- GPIO pin definitions
- Button timing constants
- Color definitions
- MQTT client ID and settings

### led_ring.py
**LEDRing class** - Complete control of WS2812 LED ring:
- Animation modes: chase, comet, spinner, rainbow, solid, flash, pulse
- Color control for each mode
- Direction control (clockwise/counter-clockwise)
- Brightness control
- Non-blocking update system

### button_handler.py
Button input handling with:
- Debouncing logic
- Press duration detection (short, long, very long)
- Pull-up resistor configuration

### config_manager.py
Configuration file management:
- `load_config()` - Load WiFi settings
- `save_config()` - Save WiFi settings
- `load_mqtt_config()` - Load MQTT settings
- `save_mqtt_config()` - Save MQTT settings

### mqtt_handler.py
MQTT functionality:
- Connection to MQTT broker
- Message callback handling
- Button press event publishing
- Ring command handlers for LED control

### ota_handler.py
Over-the-air update management:
- `init_ota()` - Initialize OTA and check for updates on boot
- `periodic_check()` - Check for updates at randomized intervals (22-26 hours)
- `check_for_updates()` - Fetch and compare versions from server
- `apply_update()` - Download files and restart device

### wifi_manager.py
WiFi connection management:
- `connect_to_wifi()` - Connect to a WiFi network
- `start_ap_mode()` - Start Access Point mode for configuration

### web_server.py
Captive portal and configuration:
- DNS server for captive portal
- Web server for configuration interface
- HTML form handling
- Configuration page generation

### main.py
Main application logic:
- Initializes all modules
- Handles WiFi connection with retry logic
- MQTT subscription and message loop
- Button press handling
- LED animation updates
- Heartbeat messages
- AP mode configuration loop

## Usage

### Running the Application

Simply upload all `.py` files to your ESP32 and run:

```python
import main
```

Or if set as `main.py`, it will run automatically on boot.

### First Time Setup

1. Power on the ESP32
2. Device will start in AP mode (LED ring shows cyan chase)
3. Connect to WiFi network: `ESP32-Setup` (password: `12345678`)
4. Browser will redirect to configuration page automatically
5. Enter your WiFi and MQTT settings
6. Device will restart and connect to your network

### Modifying LED Behavior

To change LED animations, edit the main loop in `main.py` or modify the `LEDRing` class in `led_ring.py`:

```python
# Example: Change startup animation
ring.set_mode('pulse')
ring.set_pulse_color('blue')
ring.set_pulse_range(10, 255)
```

### Adding Custom Button Actions

Modify the button handler functions in `mqtt_handler.py`:

```python
def button_long_press(client, config):
    """Handle long button press"""
    # Your custom code here
    publish_button_press('2', client, config)
```

## Dependencies

- `network` - WiFi management
- `socket` - Web server and DNS
- `machine` - Hardware control
- `neopixel` - LED control
- `time` - Timing functions
- `json` - Configuration files
- `umqtt.simple` - MQTT client

## Key Features

- **Modular Design**: Easy to understand, maintain, and extend
- **Non-blocking**: LED animations and button checks don't block main loop
- **Captive Portal**: Easy WiFi configuration through web interface
- **MQTT Support**: Remote control and monitoring
- **OTA Updates**: Over-the-air firmware updates with randomized check intervals
- **Button Control**: Local control with short/long/very-long press detection
- **Retry Logic**: Automatic WiFi reconnection attempts
- **Heartbeat**: Regular status messages via MQTT

## MQTT Topics

All topics are prefixed with the base topic configured during setup (default: `esp32/test`).

### Subscribed Topics (Commands)

| Topic | Description | Payload |
|-------|-------------|---------|
| `{topic}/ring/chase` | Chase animation | Color string or JSON |
| `{topic}/ring/static` | Solid color | Color string or JSON |
| `{topic}/ring/flash` | Flashing animation | Color string or JSON |
| `{topic}/ring/comet` | Comet with tail | Color string or JSON |
| `{topic}/ring/spinner` | Multi-arm spinner | Color string or JSON |
| `{topic}/ring/rainbow` | Rainbow cycle | Empty or JSON |
| `{topic}/ring/pulse` | Pulsing brightness | Color string or JSON |
| `{topic}/ring/reset` | Reset to default | (none) |

### Published Topics (Events)

| Topic | Description | Payload |
|-------|-------------|---------|
| `{topic}/heartbeat` | Status every 60s | `{"device": "...", "status": "alive", "uptime": 123}` |
| `{topic}/button/1` | Short press | `{"device": "...", "button": "1", "uptime": 123}` |
| `{topic}/button/2` | Long press | `{"device": "...", "button": "2", "uptime": 123}` |
| `{topic}/button/3` | Very long press | `{"device": "...", "button": "3", "uptime": 123}` |

### Command Payload Formats

Commands accept either a simple color string or a JSON object with options.

**Simple format** - just the color name:
```
red
```

**JSON format** - with optional settings:
```json
{"color": "red", "speed": 30, "brightness": 100, "direction": "cw"}
```

### Payload Options

| Option | Description | Values |
|--------|-------------|--------|
| `color` | Color name | See available colors below |
| `speed` | Animation speed (ms) | 10-1000 (lower = faster) |
| `brightness` | LED brightness | 0-255 |
| `direction` | Rotation direction | `cw`, `ccw`, `reverse` |

### Mode-Specific Options

**spinner** - supports multiple arm colors:
```json
{"colors": ["red", "green", "blue"], "speed": 30}
```

**pulse** - supports brightness range and step:
```json
{"color": "blue", "min": 10, "max": 255, "step": 5}
```

**rainbow** - no color needed, just optional speed/brightness:
```json
{"speed": 50, "brightness": 100}
```

### Available Colors

`red`, `green`, `blue`, `white`, `black`, `yellow`, `cyan`, `magenta`, `orange`, `purple`, `pink`, `lime`, `teal`, `lavender`, `brown`, `maroon`, `olive`, `navy`, `aqua`, `coral`, `gold`, `silver`, `gray`, `indigo`

### Example Commands

```bash
# Simple color
mosquitto_pub -t "esp32/test/ring/chase" -m "red"

# JSON with options
mosquitto_pub -t "esp32/test/ring/comet" -m '{"color": "purple", "speed": 40, "direction": "ccw"}'

# Spinner with multiple colors
mosquitto_pub -t "esp32/test/ring/spinner" -m '{"colors": ["red", "green", "blue"]}'

# Pulse with range
mosquitto_pub -t "esp32/test/ring/pulse" -m '{"color": "cyan", "min": 20, "max": 200, "step": 3}'

# Rainbow
mosquitto_pub -t "esp32/test/ring/rainbow" -m '{"speed": 30}'

# Reset to default
mosquitto_pub -t "esp32/test/ring/reset" -m ""
```

## OTA Updates

The device supports over-the-air firmware updates from an HTTP server.

### Configuring OTA

OTA can be configured through the web portal during initial setup, or by editing `ota_config.json`:

```json
{
  "enabled": true,
  "server_url": "http://your-server.com/firmware",
  "check_on_boot": true,
  "auto_update": true
}
```

| Setting | Description |
|---------|-------------|
| `enabled` | Enable/disable OTA updates |
| `server_url` | Base URL where firmware files are hosted |
| `check_on_boot` | Check for updates when device starts |
| `auto_update` | Automatically apply updates when found |

### Server Setup

Host a `manifest.json` file on your server with the current version and list of files:

```json
{
  "version": "1.0.1",
  "files": [
    "main.py",
    "led_ring.py",
    "mqtt_handler.py",
    "ota_handler.py"
  ]
}
```

**Server directory structure:**
```
/firmware/
├── manifest.json
├── main.py
├── led_ring.py
├── mqtt_handler.py
└── ota_handler.py
```

### Update Process

1. Device fetches `manifest.json` from `{server_url}/manifest.json`
2. Compares server version with local version in `ota_version.json`
3. If newer version available, downloads each file listed in manifest
4. Saves new version info and restarts device

### Check Timing

- **On boot**: Checks immediately if `check_on_boot` is enabled
- **Periodic**: Checks every 22-26 hours (randomized interval)

The randomized interval prevents thousands of devices from checking simultaneously and overwhelming the server.

### Manual Version Management

To set the initial version on a new device, create `ota_version.json`:

```json
{
  "version": "1.0.0",
  "files": ["main.py", "led_ring.py"],
  "updated_at": 1704470400
}
```

## Troubleshooting

### WiFi Connection Issues
- Check SSID and password in configuration
- Verify WiFi signal strength
- Check router settings (2.4GHz required for ESP32)

### MQTT Connection Issues
- Verify broker address and port
- Check username/password if required
- Ensure firewall allows MQTT traffic

### LED Ring Not Working
- Verify GPIO pin 8 connection
- Check power supply (WS2812 LEDs need adequate power)
- Verify number of LEDs matches configuration (default: 24)

### Button Not Responding
- Verify GPIO pin 5 connection
- Check pull-up resistor configuration
- Review button press duration thresholds in `constants.py`

### OTA Update Issues
- Verify server URL is accessible from device network
- Check that `manifest.json` is valid JSON
- Ensure all files listed in manifest exist on server
- Verify version in manifest is higher than local version
- Check device has sufficient memory for downloads

## Customization

### Changing Default Values

Edit `constants.py`:
```python
BUTTON_PIN = 5              # Change button GPIO
LONG_PRESS_TIME = 3000      # Change long press threshold
MQTT_KEEPALIVE = 60         # Change MQTT keepalive
```

### Adding New LED Modes

Add to `led_ring.py`:
```python
def my_custom_animation(self):
    """My custom LED animation"""
    # Your animation code here
    pass

# Then in update():
elif self.mode == 'my_mode':
    self.my_custom_animation()
```

### Adding New MQTT Topics

Add to subscription list in `main.py`:
```python
ring_topics = [
    # ... existing topics
    f'{base_topic}/my/custom/topic'
]
```

## License

[Your license here]

## Contributing

[Your contribution guidelines here]
