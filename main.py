"""
Main Program
Ties all modules together and implements the main application logic
"""

import machine
import time
import json

from constants import MAX_RETRIES, MQTT_CLIENT_ID
from led_ring import LEDRing
from button_handler import (
    setup_button,
    check_button,
    button_short_press,
    button_long_press,
    button_very_long_press
)
from config_manager import load_config, load_mqtt_config
from mqtt_handler import (
    connect_to_mqtt,
    mqtt_callback,
    set_ring
)
from wifi_manager import connect_to_wifi, start_ap_mode, is_wifi_connected
from web_server import (
    setup_dns_server,
    handle_dns_request,
    setup_web_server,
    handle_web_request
)
from ota_handler import init_ota, periodic_check


def main():
    """Main program logic"""
    global ring, mqtt_client, mqtt_config
    
    config = load_config()

    # Initialize LED ring on GPIO 8
    ring = LEDRing(pin=8, num_leds=24)
    ring.set_update_interval(30)
    ring.set_brightness(50)

    # Set initial direction
    ring.set_direction('cw')  # or 'ccw', 1, -1, 'reverse'

    # Pass ring reference to mqtt_handler for command handling
    set_ring(ring)

    ring.clear()
    
    if config:
        print('Found saved WiFi configuration')
        ssid = config['ssid']
        password = config['password']
        
        # Try to connect with retry logic
        retry_count = 0
        connected = False
        
        while retry_count < MAX_RETRIES and not connected:
            retry_count += 1
            print(f'Connection attempt {retry_count}/{MAX_RETRIES}')
            
            connected = connect_to_wifi(ssid, password)
            
            if not connected and retry_count < MAX_RETRIES:
                print('Retrying in 5 seconds...')
                time.sleep(5)
        
        if connected:
            print('Device is online!')
            ring.set_mode('chase')
            ring.set_chase_color('green')

            # Initialize OTA and check for updates on boot
            init_ota(ring)

            # Load MQTT configuration and connect
            mqtt_config = load_mqtt_config()
            mqtt_client = connect_to_mqtt(mqtt_config)
            
            if mqtt_client:
                # Set callback for incoming messages
                mqtt_client.set_callback(mqtt_callback)
                
                # Subscribe to ring command topics
                base_topic = mqtt_config['topic']
                ring_topics = [
                    f'{base_topic}/ring/chase',
                    f'{base_topic}/ring/static',
                    f'{base_topic}/ring/flash',
                    f'{base_topic}/ring/comet',
                    f'{base_topic}/ring/spinner',
                    f'{base_topic}/ring/rainbow',
                    f'{base_topic}/ring/pulse',
                    f'{base_topic}/ring/reset',
                    f'{base_topic}/command',
                    f'{base_topic}/button/#'
                ]
                
                for topic in ring_topics:
                    mqtt_client.subscribe(topic)
                    print(f'Subscribed to: {topic}')
                      
                # Setup button for direction control
                button = setup_button()
                
                # Main loop - keep MQTT connection alive
                print('Running main loop...')
                last_heartbeat = time.ticks_ms()
                heartbeat_interval = 60000  # 60 seconds in milliseconds

                # WiFi monitoring state
                last_wifi_check = time.ticks_ms()
                wifi_check_interval = 5000  # Check WiFi every 5 seconds
                wifi_was_connected = True
                saved_ring_state = None

                while True:
                    try:
                        # Update LEDs (non-blocking)
                        ring.update()
            
                        # Check for button press
                        button_press = check_button(button)
                        if button_press == 'short':
                            button_short_press(mqtt_client, mqtt_config)
                            ring.reverse_direction()
                        elif button_press == 'long':
                            button_long_press(mqtt_client, mqtt_config)
                        elif button_press == 'very_long':
                            button_very_long_press(mqtt_client, mqtt_config)
                            
                        # Check for messages (non-blocking)
                        mqtt_client.check_msg()
                        
                        # Check if 60 seconds have passed since last heartbeat
                        current_time = time.ticks_ms()
                        if time.ticks_diff(current_time, last_heartbeat) >= heartbeat_interval:
                            # Publish heartbeat message
                            heartbeat_msg = json.dumps({
                                'device': MQTT_CLIENT_ID,
                                'status': 'alive',
                                'uptime': time.ticks_ms() // 1000
                            })
                            mqtt_client.publish(mqtt_config['topic'] + '/heartbeat', heartbeat_msg)
                            print('Heartbeat sent:', time.ticks_ms())
                            last_heartbeat = current_time

                        # Check WiFi connection status periodically
                        if time.ticks_diff(current_time, last_wifi_check) >= wifi_check_interval:
                            last_wifi_check = current_time
                            wifi_connected = is_wifi_connected()

                            if wifi_was_connected and not wifi_connected:
                                # WiFi just lost - save state and switch to yellow pulse
                                print('WiFi connection lost!')
                                saved_ring_state = ring.save_state()
                                ring.set_mode('pulse')
                                ring.set_pulse_color('yellow')
                                ring.set_pulse_range(20, 200)
                                ring.set_pulse_step(5)
                                wifi_was_connected = False

                            elif not wifi_was_connected and wifi_connected:
                                # WiFi restored - restore previous state
                                print('WiFi connection restored!')
                                if saved_ring_state:
                                    ring.restore_state(saved_ring_state)
                                    saved_ring_state = None
                                wifi_was_connected = True

                        # Periodic OTA update check (22-26 hours random interval)
                        periodic_check()

                        # Small delay to prevent tight loop
                        time.sleep_ms(50)
                        
                    except Exception as e:
                        print(f'MQTT error: {e}')
                        # Try to reconnect
                        try:
                            mqtt_client.connect()
                            print('MQTT reconnected')
                        except:
                            print('MQTT reconnection failed')
                            break
            else:
                print('MQTT connection failed, but WiFi is connected')
                # Your main application code without MQTT goes here
                ring.set_mode('pulse')
                ring.set_pulse_color('red')    # Pulse mode color
                ring.set_pulse_range(10, 100)     # Very gentle pulse
                ring.set_pulse_step(5)
                while True:
                    # Update LEDs (non-blocking)
                    ring.update()
                    time.sleep_ms(5)
        else:
            print(f'Failed to connect after {MAX_RETRIES} attempts')
            print('Entering AP configuration mode...')
            ring.set_mode('chase')
            ring.set_chase_color('red')
    else:
        print('No WiFi configuration found')
        ring.set_mode('chase')
        ring.set_chase_color('cyan')
            
    # Start AP mode if no config or connection failed
    ap = start_ap_mode()
    ap_ip = ap.ifconfig()[0]
    
    # Setup button for AP mode too
    button = setup_button()
    
    server_socket = setup_web_server()
    dns_socket = setup_dns_server()
    
    # Real-time loop for AP mode
    print('Waiting for configuration...')
    while True:
        # Check for button press
        button_press = check_button(button)
        if button_press == 'short':
            print('Short button press detected in AP mode!')
            ring.reverse_direction()
        elif button_press == 'long':
            print('Long button press detected in AP mode!')
        elif button_press == 'very_long':
            print('Very long button press detected in AP mode!')
            
        # Handle DNS requests (redirect all domains to our IP)
        if dns_socket:
            handle_dns_request(dns_socket, ap_ip)
            
        # Handle web server requests (non-blocking)
        config_received = handle_web_request(server_socket)
        
        if config_received:
            print('Configuration received, restarting...')
            server_socket.close()
            if dns_socket:
                dns_socket.close()
            time.sleep(2)
            machine.reset()
        
        # Update LEDs (non-blocking)
        ring.update()
        time.sleep_ms(100)  # Small delay to prevent tight loop


# Run the main program
if __name__ == '__main__':
    main()
