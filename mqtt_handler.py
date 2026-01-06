"""
MQTT Handler Module
Handles MQTT connection, message callbacks, and button press events
"""

import json
import time
from umqtt.simple import MQTTClient
from constants import MQTT_CLIENT_ID, MQTT_KEEPALIVE


# Module-level variables (to be set by main)
mqtt_client = None
mqtt_config = None


def connect_to_mqtt(config):
    """Connect to MQTT broker and send test message"""
    try:
        print('Connecting to MQTT broker...')
        print(f'Broker: {config["broker"]}:{config["port"]}')
        
        # Create MQTT client
        client = MQTTClient(
            client_id=MQTT_CLIENT_ID,
            server=config['broker'],
            port=config['port'],
            user=config['username'] if config['username'] else None,
            password=config['password'] if config['password'] else None,
            keepalive=MQTT_KEEPALIVE
        )
        
        # Connect to broker
        client.connect()
        print('Connected to MQTT broker!')
        
        # Publish test message
        test_topic = config['topic']
        test_message = json.dumps({
            'device': MQTT_CLIENT_ID,
            'status': 'online',
            'message': 'ESP32 connected successfully',
            'timestamp': time.time()
        })
        
        client.publish(test_topic, test_message)
        print(f'Published test message to topic: {test_topic}')
        print(f'Message: {test_message}')
        
        return client
        
    except Exception as e:
        print(f'MQTT connection failed: {e}')
        return None


def mqtt_callback(topic, msg):
    """Callback for incoming MQTT messages"""
    try:
        topic_str = topic.decode('utf-8')
        msg_str = msg.decode('utf-8')
        print(f'Received message on {topic_str}: {msg_str}')
        
        # Parse the topic to get the command
        topic_parts = topic_str.split('/')
        
        if len(topic_parts) >= 2:
            command = topic_parts[-1]  # Last part of topic (e.g., 'chase', 'static', 'reset')
            
            # Handle ring commands with color data
            if 'ring' in topic_str:
                if command == 'chase':
                    ring_chase(msg_str)
                elif command == 'static':
                    ring_static(msg_str)
                elif command == 'flash':
                    ring_flash(msg_str)
                elif command == 'comet':
                    ring_comet(msg_str)
                elif command == 'reset':
                    ring_reset()
                else:
                    print(f'Unknown ring command: {command}')
    except Exception as e:
        print(f'MQTT callback error: {e}')


def mqtt_publish_button_press(button_type, client, config):
    """Publish button press message to MQTT
    Args:
        button_type: '1' for short, '2' for long, '3' for very long
        client: MQTT client instance
        config: MQTT configuration dict
    """
    heartbeat_msg = json.dumps({
        'device': MQTT_CLIENT_ID,
        'button': button_type,
        'uptime': time.ticks_ms() // 1000
    })
    client.publish(config['topic'] + f'/button/{button_type}', heartbeat_msg)
    print(f'Button press sent: {time.ticks_ms()}')


# Ring command handlers (placeholder implementations)
def ring_chase(color):
    """Ring chase animation with specified color"""
    print(f'[RING CHASE] Starting chase animation with color: {color}')
    print(f'[RING CHASE] Animation would cycle LEDs in sequence')
    # TODO: Implement your LED ring chase animation here


def ring_static(color):
    """Ring static color display"""
    print(f'[RING STATIC] Setting static color: {color}')
    print(f'[RING STATIC] All LEDs would display this color continuously')
    # TODO: Implement your LED ring static color display here


def ring_flash(color):
    """Ring flash animation with specified color"""
    print(f'[RING FLASH] Starting flash animation with color: {color}')
    print(f'[RING FLASH] LEDs would flash on/off repeatedly')
    # TODO: Implement your LED ring flash animation here


def ring_comet(color):
    """Ring comet animation with specified color"""
    print(f'[RING COMET] Starting comet animation with color: {color}')
    print(f'[RING COMET] A trailing comet effect would move around the ring')
    # TODO: Implement your LED ring comet animation here


def ring_reset():
    """Reset ring to default state (off or default color)"""
    print(f'[RING RESET] Resetting ring to default state')
    print(f'[RING RESET] All LEDs would turn off or return to default')
    # TODO: Implement your LED ring reset here


