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
- Ring command handlers (placeholders for implementation)

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

### Implementing MQTT Commands

The placeholder functions in `mqtt_handler.py` can be implemented to control the LED ring:

```python
def ring_chase(color):
    """Ring chase animation with specified color"""
    # Access the global ring object
    global ring
    ring.set_mode('chase')
    ring.set_chase_color(color)
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
- **Button Control**: Local control with short/long/very-long press detection
- **Retry Logic**: Automatic WiFi reconnection attempts
- **Heartbeat**: Regular status messages via MQTT

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
