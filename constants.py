"""
Constants and configuration values shared across modules
"""

import machine

# Firmware version
VERSION = '1.0.0'

# Configuration file paths
CONFIG_FILE = 'wifi_config.json'
MQTT_CONFIG_FILE = 'mqtt_config.json'
MAX_RETRIES = 3

# MQTT Configuration
MQTT_CLIENT_ID = 'esp32_' + ''.join('{:02x}'.format(b) for b in machine.unique_id())
MQTT_KEEPALIVE = 60

# DNS Server Configuration
DNS_PORT = 53

# GPIO Configuration for "touch" button
BUTTON_PIN = 5
DEBOUNCE_TIME = 50              # milliseconds
LONG_PRESS_TIME = 2500          # milliseconds (2.5 seconds)
VERY_LONG_PRESS_TIME = 7000     # milliseconds (7 seconds)
                                # Adjusted for capacitive touch button behavior
                                #    (Auto sends a release at 7.1 seconds)
                                # Note: Capacitive touch buttons may require different timing

# Color name dictionary
COLORS = {
    'red': (255, 0, 0),
    'green': (0, 255, 0),
    'blue': (0, 0, 255),
    'yellow': (255, 255, 0),
    'cyan': (0, 255, 255),
    'magenta': (255, 0, 255),
    'white': (255, 255, 255),
    'orange': (255, 165, 0),
    'purple': (128, 0, 128),
    'pink': (255, 192, 203),
    'lime': (0, 255, 0),
    'teal': (0, 128, 128),
    'lavender': (230, 230, 250),
    'brown': (165, 42, 42),
    'beige': (245, 245, 220),
    'maroon': (128, 0, 0),
    'mint': (189, 252, 201),
    'olive': (128, 128, 0),
    'coral': (255, 127, 80),
    'navy': (0, 0, 128),
    'grey': (128, 128, 128),
    'gray': (128, 128, 128),
    'black': (0, 0, 0),
    'off': (0, 0, 0)
}
