"""
MQTT Handler Module
Handles MQTT connection, message callbacks, and button press events
"""

import json
import time
from umqtt.simple import MQTTClient
from constants import MQTT_CLIENT_ID, MQTT_KEEPALIVE, VERSION
from ota_handler import check_for_updates, apply_update, get_ota_status


# Module-level variables (to be set by main)
mqtt_client = None
mqtt_config = None
ring = None


def set_ring(ring_instance):
    """Set the ring reference for command handlers.
    Call this from main.py after creating the LEDRing instance.
    """
    global ring
    ring = ring_instance


def set_mqtt_client(client, config):
    """Set the MQTT client and config for publishing responses.
    Call this from main.py after connecting to MQTT.
    """
    global mqtt_client, mqtt_config
    mqtt_client = client
    mqtt_config = config


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
            'version': VERSION,
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
                match command:
                    case 'chase':
                        ring_chase(msg_str)
                    case 'static':
                        ring_static(msg_str)
                    case 'flash':
                        ring_flash(msg_str)
                    case 'comet':
                        ring_comet(msg_str)
                    case 'spinner':
                        ring_spinner(msg_str)
                    case 'rainbow':
                        ring_rainbow(msg_str)
                    case 'pulse':
                        ring_pulse(msg_str)
                    case 'reset':
                        ring_reset()
                    case _:
                        print(f'Unknown ring command: {command}')

            # Handle OTA commands
            elif 'ota' in topic_str:
                match command:
                    case 'check':
                        ota_check(msg_str)
                    case 'update':
                        ota_update(msg_str)
                    case 'status':
                        ota_status(msg_str)
                    case _:
                        print(f'Unknown OTA command: {command}')
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


# Ring command handlers
def _parse_command_payload(payload):
    """Parse MQTT payload - supports JSON or plain color string.

    JSON format: {"color": "red", "speed": 30, "brightness": 100, "direction": "cw"}
    Plain format: "red" (just the color name)

    Returns dict with parsed values and defaults.
    """
    defaults = {
        'color': 'white',
        'speed': None,
        'brightness': None,
        'direction': None
    }

    payload = payload.strip()

    # Try JSON first
    if payload.startswith('{'):
        try:
            data = json.loads(payload)
            return {
                'color': data.get('color', defaults['color']),
                'speed': data.get('speed', defaults['speed']),
                'brightness': data.get('brightness', defaults['brightness']),
                'direction': data.get('direction', defaults['direction'])
            }
        except:
            pass

    # Plain color string
    if payload:
        defaults['color'] = payload

    return defaults


def _apply_common_settings(params):
    """Apply common settings (speed, brightness, direction) if provided."""
    global ring
    if ring is None:
        return

    if params['speed'] is not None:
        ring.set_update_interval(params['speed'])

    if params['brightness'] is not None:
        ring.set_brightness(params['brightness'])

    if params['direction'] is not None:
        ring.set_direction(params['direction'])


def ring_chase(payload):
    """Ring chase animation with specified color.

    Payload: "red" or {"color": "red", "speed": 30, "brightness": 100}
    """
    global ring
    if ring is None:
        print('[RING CHASE] Error: ring not initialized')
        return

    params = _parse_command_payload(payload)
    print(f'[RING CHASE] Starting chase animation with color: {params["color"]}')

    _apply_common_settings(params)
    ring.set_chase_color(params['color'])
    ring.set_mode('chase')


def ring_static(payload):
    """Ring static color display.

    Payload: "blue" or {"color": "blue", "brightness": 50}
    """
    global ring
    if ring is None:
        print('[RING STATIC] Error: ring not initialized')
        return

    params = _parse_command_payload(payload)
    print(f'[RING STATIC] Setting static color: {params["color"]}')

    _apply_common_settings(params)
    ring.set_solid_color(params['color'])
    ring.set_mode('solid')


def ring_flash(payload):
    """Ring flash animation with specified color.

    Payload: "yellow" or {"color": "yellow", "speed": 200}
    """
    global ring
    if ring is None:
        print('[RING FLASH] Error: ring not initialized')
        return

    params = _parse_command_payload(payload)
    print(f'[RING FLASH] Starting flash animation with color: {params["color"]}')

    _apply_common_settings(params)
    ring.set_flash_color(params['color'])
    ring.set_mode('flash')


def ring_comet(payload):
    """Ring comet animation with specified color.

    Payload: "purple" or {"color": "purple", "speed": 40, "direction": "ccw"}
    """
    global ring
    if ring is None:
        print('[RING COMET] Error: ring not initialized')
        return

    params = _parse_command_payload(payload)
    print(f'[RING COMET] Starting comet animation with color: {params["color"]}')

    _apply_common_settings(params)
    ring.set_comet_color(params['color'])
    ring.set_mode('comet')


def ring_reset():
    """Reset ring to default state (green chase animation)."""
    global ring
    if ring is None:
        print('[RING RESET] Error: ring not initialized')
        return

    print('[RING RESET] Resetting ring to default state')
    ring.set_brightness(50)
    ring.set_update_interval(30)
    ring.set_direction('cw')
    ring.set_chase_color('green')
    ring.set_mode('chase')


def ring_spinner(payload):
    """Ring spinner animation with multiple colored arms.

    Payload: "red" (single color for all arms)
             or {"colors": ["red", "green", "blue"], "speed": 30}
    """
    global ring
    if ring is None:
        print('[RING SPINNER] Error: ring not initialized')
        return

    params = _parse_command_payload(payload)

    # Check for colors array in JSON payload
    payload = payload.strip()
    colors = None
    if payload.startswith('{'):
        try:
            data = json.loads(payload)
            if 'colors' in data:
                colors = data['colors']
        except:
            pass

    if colors:
        print(f'[RING SPINNER] Starting spinner with colors: {colors}')
        ring.set_spinner_colors(colors)
    else:
        # Use single color for all 3 arms
        color = params['color']
        print(f'[RING SPINNER] Starting spinner with color: {color}')
        ring.set_spinner_colors([color, color, color])

    _apply_common_settings(params)
    ring.set_mode('spinner')


def ring_rainbow(payload):
    """Ring rainbow cycle animation.

    Payload: "" (empty) or {"speed": 50, "brightness": 100}
    """
    global ring
    if ring is None:
        print('[RING RAINBOW] Error: ring not initialized')
        return

    print('[RING RAINBOW] Starting rainbow cycle animation')
    params = _parse_command_payload(payload)
    _apply_common_settings(params)
    ring.set_mode('rainbow_cycle')


def ring_pulse(payload):
    """Ring pulse animation - all LEDs pulse between min and max brightness.

    Payload: "blue" or {"color": "blue", "min": 10, "max": 255, "step": 5}
    """
    global ring
    if ring is None:
        print('[RING PULSE] Error: ring not initialized')
        return

    params = _parse_command_payload(payload)
    print(f'[RING PULSE] Starting pulse animation with color: {params["color"]}')

    # Parse pulse-specific settings from JSON
    payload = payload.strip()
    if payload.startswith('{'):
        try:
            data = json.loads(payload)
            if 'min' in data or 'max' in data:
                min_val = data.get('min', 10)
                max_val = data.get('max', 255)
                ring.set_pulse_range(min_val, max_val)
            if 'step' in data:
                ring.set_pulse_step(data['step'])
        except:
            pass

    _apply_common_settings(params)
    ring.set_pulse_color(params['color'])
    ring.set_mode('pulse')


# OTA command handlers
def ota_check(payload):
    """Check for OTA updates and publish result.

    Payload: ignored (can be empty)
    """
    print('[OTA] MQTT triggered update check')
    update_info = check_for_updates(force=True)

    if update_info:
        result = {
            'device': MQTT_CLIENT_ID,
            'available': update_info.get('available', False),
            'current_version': update_info.get('current_version', '0.0.0'),
            'new_version': update_info.get('new_version', '0.0.0')
        }
        print(f'[OTA] Check result: {result}')
        _publish_ota_response('check', result)
    else:
        _publish_ota_response('check', {
            'device': MQTT_CLIENT_ID,
            'error': 'Check failed or OTA disabled'
        })


def ota_update(payload):
    """Apply OTA update if available.

    Payload: ignored (can be empty)
    """
    print('[OTA] MQTT triggered update apply')
    update_info = check_for_updates(force=True)

    if update_info and update_info.get('available', False):
        _publish_ota_response('update', {
            'device': MQTT_CLIENT_ID,
            'status': 'starting',
            'new_version': update_info.get('new_version', '0.0.0')
        })
        # This will restart the device if successful
        apply_update(update_info)
    else:
        _publish_ota_response('update', {
            'device': MQTT_CLIENT_ID,
            'status': 'no_update',
            'message': 'No update available'
        })


def ota_status(payload):
    """Publish current OTA status.

    Payload: ignored (can be empty)
    """
    print('[OTA] MQTT requested status')
    status = get_ota_status()
    status['device'] = MQTT_CLIENT_ID
    _publish_ota_response('status', status)


def _publish_ota_response(command, data):
    """Publish OTA response to MQTT."""
    global mqtt_client, mqtt_config
    if mqtt_client and mqtt_config:
        topic = mqtt_config['topic'] + f'/ota/{command}/response'
        mqtt_client.publish(topic, json.dumps(data))
        print(f'[OTA] Published response to {topic}')
