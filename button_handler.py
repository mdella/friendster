"""
Button Handler Module
Handles button input with debouncing and press duration detection
"""

from machine import Pin
from mqtt_handler import mqtt_publish_button_press
import time
from constants import BUTTON_PIN, DEBOUNCE_TIME, LONG_PRESS_TIME, VERY_LONG_PRESS_TIME


# Global button state
__button_normal_state__ = 0     # Assuming pull-up resistor, button not pressed is HIGH
                                # Note: Using capacitive touch buttons may invert this logic
__button_last_state__ = 0       # Assume button not pressed initially
__button_press_start__ = 0
__button_state_change_time__ = 0


def setup_button():
    """Setup button on GPIO 5 with pull-up resistor"""
    button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
    print(f'Button configured on GPIO {BUTTON_PIN} with pull-up')
    return button


def check_button(button):
    """Check button state with debouncing. Returns 'short', 'long', 'very_long', or None."""
    global __button_last_state__, __button_state_change_time__, __button_press_start__
    
    current_state = button.value()
    current_time = time.ticks_ms()
    
    # Check if enough time has passed since last state change (debounce)
    if time.ticks_diff(current_time,__button_state_change_time__) > DEBOUNCE_TIME:

        # Button just pressed
        if __button_last_state__ != current_state and current_state == __button_normal_state__ ^ 1:
            __button_last_state__ = current_state
            __button_press_start__ = current_time
            __button_state_change_time__ = current_time
            return None
        
        # Button just released
        elif __button_last_state__ != current_state and current_state == __button_normal_state__:
            __button_last_state__ = current_state
            __button_state_change_time__ = current_time
            
            # Calculate press duration
            press_duration = time.ticks_diff(current_time, __button_press_start__)
            print("press_duration:          ", press_duration)
            
            # Check what type of press it was based on duration
            if press_duration >= VERY_LONG_PRESS_TIME:
                # Released after 15+ seconds (very long press)
                return 'very_long'
            elif press_duration >= LONG_PRESS_TIME:
                # Released in the long press window (3-15 seconds)
                return 'long'
            else:
                # Released before long press threshold (short press)
                return 'short'
        
        # Update state if it changed.
        # Only used in debounce edge cases through jitter
        if __button_last_state__ != current_state:
            __button_last_state__ = current_state
            __button_state_change_time__ = current_time
    return None


def button_short_press(client, config):
    """Handle short button press - reverse animation direction"""
    print(f'[BUTTON SHORT] Short press action')
    print(f'[RING DIRECTION] Reversing animation direction')
    mqtt_publish_button_press('1', client, config)


def button_long_press(client, config):
    """Handle long button press - toggle brightness"""
    print(f'[BUTTON LONG] Long press action')
    print(f'[RING BRIGHTNESS] Toggling brightness level')
    mqtt_publish_button_press('2', client, config)


def button_very_long_press(client, config):
    """Handle very long button press - factory reset"""
    print(f'[BUTTON VERY LONG] Very long press action')
    print(f'[FACTORY RESET] Initiating factory reset!')
    mqtt_publish_button_press('3', client, config)
    # Uncomment below for actual factory reset
    """
    try:
        import os
        from constants import CONFIG_FILE, MQTT_CONFIG_FILE
        os.remove(CONFIG_FILE)
        os.remove(MQTT_CONFIG_FILE)
        print(f'[FACTORY RESET] Configuration files deleted')
        print(f'[FACTORY RESET] Restarting in AP mode...')
        time.sleep(2)
        import machine
        machine.reset()
    except:
        print(f'[FACTORY RESET] No configuration files to delete')
        print(f'[FACTORY RESET] Restarting anyway...')
        time.sleep(2)
        import machine
        machine.reset()
    """

