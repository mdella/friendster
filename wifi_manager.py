"""
WiFi Manager Module
Handles WiFi connection and Access Point mode
"""

import network
import time


def connect_to_wifi(ssid, password):
    """Connect to WiFi network"""
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    
    if sta.isconnected():
        print('Already connected, disconnecting first...')
        sta.disconnect()
        time.sleep(1)
    
    print(f'Connecting to {ssid}...')
    sta.connect(ssid, password)
    
    # Wait for connection (30 seconds timeout)
    timeout = 30
    while not sta.isconnected() and timeout > 0:
        time.sleep(1)
        timeout -= 1
        print('.', end='')
    
    print()
    
    if sta.isconnected():
        print('Connected successfully!')
        print('IP:', sta.ifconfig()[0])
        return True
    else:
        print('Connection failed')
        return False


def start_ap_mode():
    """Start Access Point mode"""
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    
    # Configure AP with specific settings
    ap.config(essid='ESP32-Setup', password='12345678')
    ap.config(authmode=3)  # WPA2
    
    while not ap.active():
        time.sleep(0.1)
    
    print('AP Mode Started')
    print('SSID: ESP32-Setup')
    print('Password: 12345678')
    print('IP:', ap.ifconfig()[0])
    
    return ap
