"""
Configuration Manager Module
Handles loading and saving WiFi and MQTT configuration files
"""

import json
from constants import CONFIG_FILE, MQTT_CONFIG_FILE


def load_config():
    """Load WiFi configuration from file"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return None


def save_config(ssid, password):
    """Save WiFi configuration to file"""
    config = {'ssid': ssid, 'password': password}
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)


def load_mqtt_config():
    """Load MQTT configuration from file"""
    try:
        with open(MQTT_CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        # Default MQTT configuration
        return {
            'broker': 'broker.hivemq.com',
            'port': 1883,
            'topic': 'esp32/test',
            'username': '',
            'password': ''
        }


def save_mqtt_config(broker, port, topic, username, password):
    """Save MQTT configuration to file"""
    config = {
        'broker': broker,
        'port': port,
        'topic': topic,
        'username': username,
        'password': password
    }
    with open(MQTT_CONFIG_FILE, 'w') as f:
        json.dump(config, f)
