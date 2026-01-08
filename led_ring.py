"""
LED Ring Control Module
Handles WS2812 Ring LED animations and control
"""

from machine import Pin
import neopixel
import time
from constants import COLORS


class LEDRing:
    def __init__(self, pin=8, num_leds=24):
        self.np = neopixel.NeoPixel(Pin(pin), num_leds)
        self.num_leds = num_leds
        self.position = 0
        self.last_update = 0
        self.update_interval = 50  # milliseconds between LED updates
        self.brightness = 50  # 0-255
        self.active = True
        self.mode = 'chase'  # Current animation mode
        self.hue = 0  # For rainbow effect
        self.direction = 1  # 1 for clockwise, -1 for counter-clockwise
        
        # Color settings for different modes
        self.chase_color = (255, 0, 0)  # Red
        self.comet_color = (0, 150, 255)  # Blue
        self.spinner_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]  # RGB arms
        self.solid_color = (255, 255, 255)  # White
        self.flash_color = (255, 0, 0)  # Red
        self.flash_state = False  # For flashing mode
        self.pulse_color = (0, 150, 255)  # Blue
        self.pulse_min_brightness = 10  # Minimum brightness for pulse
        self.pulse_max_brightness = 255  # Maximum brightness for pulse
        self.pulse_current = 10  # Current pulse brightness level
        self.pulse_direction = 1  # 1 for increasing, -1 for decreasing
        self.pulse_step = 5  # How much to change brightness each update
        
    def set_update_interval(self, ms):
        """Set how fast the LEDs move (milliseconds)"""
        self.update_interval = ms
        
    def set_brightness(self, brightness):
        """Set brightness 0-255"""
        self.brightness = max(0, min(255, brightness))
        
    def set_direction(self, direction):
        """Set rotation direction.
        direction: 'cw' or 'clockwise' or 1 for clockwise
                   'ccw' or 'counter-clockwise' or -1 for counter-clockwise
                   'reverse' to flip current direction
        """
        if isinstance(direction, str):
            direction_lower = direction.lower()
            if direction_lower in ['cw', 'clockwise']:
                self.direction = 1
            elif direction_lower in ['ccw', 'counter-clockwise', 'counterclockwise']:
                self.direction = -1
            elif direction_lower == 'reverse':
                self.direction *= -1
            else:
                print(f"Warning: Unknown direction '{direction}', use 'cw', 'ccw', or 'reverse'")
        elif direction in [1, -1]:
            self.direction = direction
        else:
            print("Warning: Direction must be 1 (cw), -1 (ccw), or 'reverse'")
        
    def reverse_direction(self):
        """Reverse the current rotation direction"""
        self.direction *= -1
        
    def set_mode(self, mode):
        """Set animation mode: 'solid', 'flash', 'pulse', 'chase', 'comet', 'spinner', 'rainbow_cycle'"""
        self.mode = mode
        self.position = 0
        self.flash_state = False
        
    def _parse_color(self, color):
        """Convert color name or RGB tuple to RGB tuple"""
        if isinstance(color, str):
            color_lower = color.lower()
            if color_lower in COLORS:
                return COLORS[color_lower]
            else:
                print(f"Warning: Unknown color '{color}', using red")
                return (255, 0, 0)
        elif isinstance(color, (tuple, list)) and len(color) == 3:
            return tuple(color)
        else:
            print(f"Warning: Invalid color format, using red")
            return (255, 0, 0)
        
    def set_chase_color(self, *args):
        """Set the color for chase mode.
        Can be called as:
          set_chase_color('red')
          set_chase_color(255, 0, 0)
          set_chase_color((255, 0, 0))
        """
        if len(args) == 1:
            self.chase_color = self._parse_color(args[0])
        elif len(args) == 3:
            self.chase_color = (args[0], args[1], args[2])
        else:
            print("Invalid arguments for set_chase_color")
        
    def set_comet_color(self, *args):
        """Set the color for comet mode.
        Can be called as:
          set_comet_color('blue')
          set_comet_color(0, 0, 255)
          set_comet_color((0, 0, 255))
        """
        if len(args) == 1:
            self.comet_color = self._parse_color(args[0])
        elif len(args) == 3:
            self.comet_color = (args[0], args[1], args[2])
        else:
            print("Invalid arguments for set_comet_color")
        
    def set_spinner_colors(self, colors):
        """Set colors for spinner arms. 
        Can be list of color names or RGB tuples.
        Examples:
          set_spinner_colors(['red', 'green', 'blue'])
          set_spinner_colors([(255,0,0), (0,255,0), (0,0,255)])
          set_spinner_colors(['red', (0,255,0), 'blue'])  # Mixed!
        """
        self.spinner_colors = [self._parse_color(c) for c in colors]
        
    def set_solid_color(self, *args):
        """Set the color for solid mode.
        Can be called as:
          set_solid_color('white')
          set_solid_color(255, 255, 255)
          set_solid_color((255, 255, 255))
        """
        if len(args) == 1:
            self.solid_color = self._parse_color(args[0])
        elif len(args) == 3:
            self.solid_color = (args[0], args[1], args[2])
        else:
            print("Invalid arguments for set_solid_color")
    
    def set_flash_color(self, *args):
        """Set the color for flashing mode.
        Can be called as:
          set_flash_color('red')
          set_flash_color(255, 0, 0)
          set_flash_color((255, 0, 0))
        """
        if len(args) == 1:
            self.flash_color = self._parse_color(args[0])
        elif len(args) == 3:
            self.flash_color = (args[0], args[1], args[2])
        else:
            print("Invalid arguments for set_flash_color")
            
    def set_pulse_color(self, *args):
        """Set the color for pulse mode.
        Can be called as:
          set_pulse_color('blue')
          set_pulse_color(0, 150, 255)
          set_pulse_color((0, 150, 255))
        """
        if len(args) == 1:
            self.pulse_color = self._parse_color(args[0])
        elif len(args) == 3:
            self.pulse_color = (args[0], args[1], args[2])
        else:
            print("Invalid arguments for set_pulse_color")
            
    def set_pulse_range(self, min_brightness, max_brightness):
        """Set the brightness range for pulse mode (0-255).
        Args:
            min_brightness: Minimum brightness level (0-255)
            max_brightness: Maximum brightness level (0-255)
        """
        self.pulse_min_brightness = max(0, min(255, min_brightness))
        self.pulse_max_brightness = max(0, min(255, max_brightness))
        # Ensure min is less than max
        if self.pulse_min_brightness > self.pulse_max_brightness:
            self.pulse_min_brightness, self.pulse_max_brightness = \
                self.pulse_max_brightness, self.pulse_min_brightness
    
    def set_pulse_step(self, step):
        """Set how fast the pulse changes (higher = faster pulse).
        Args:
            step: Brightness change per update (1-50 recommended)
        """
        self.pulse_step = max(1, min(50, step))
            
    def wheel(self, pos):
        """Generate rainbow colors across 0-255 positions"""
        pos = pos % 256
        if pos < 85:
            return (pos * 3, 255 - pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return (255 - pos * 3, 0, pos * 3)
        else:
            pos -= 170
            return (0, pos * 3, 255 - pos * 3)
    
    def scale_color(self, color, scale):
        """Scale a color tuple by a factor (0.0 to 1.0)"""
        return tuple(int(c * scale * self.brightness / 255) for c in color)
    
    def clear(self):
        """Turn off all LEDs"""
        for i in range(self.num_leds):
            self.np[i] = (0, 0, 0)
        self.np.write()
        
    def chase(self):
        """Single LED chasing around the ring with trail"""
        self.clear()
        b = self.brightness
        color = self.chase_color
        self.np[self.position] = self.scale_color(color, 1.0)  # Main LED
        self.np[(self.position - self.direction) % self.num_leds] = self.scale_color(color, 0.33)  # Trail
        self.np[(self.position - 2 * self.direction) % self.num_leds] = self.scale_color(color, 0.16)  # Fading trail
        self.np.write()
        
    def comet(self):
        """Comet effect with long fading tail"""
        self.clear()
        # Draw comet head and tail
        tail_length = 8
        for i in range(tail_length):
            led_pos = (self.position - i) % self.num_leds
            # Exponential fade for more realistic comet
            intensity = (tail_length - i) / tail_length
            intensity = intensity ** 2  # Square for exponential fade
            color = self.scale_color(self.comet_color, intensity)
            self.np[led_pos] = color
        self.np.write()
        
    def spinner(self):
        """Multiple LEDs spinning (opposite sides lit)"""
        self.clear()
        num_arms = len(self.spinner_colors)
        for arm in range(num_arms):
            led_pos = (self.position + (self.num_leds // num_arms) * arm) % self.num_leds
            color = self.scale_color(self.spinner_colors[arm], 1.0)
            self.np[led_pos] = color
            # Add slight trail
            self.np[(led_pos - 1) % self.num_leds] = self.scale_color(self.spinner_colors[arm], 0.3)
        self.np.write()
        
    def rainbow_cycle(self):
        """Rainbow that cycles around the ring"""
        for i in range(self.num_leds):
            # Calculate color based on position and animation frame
            pixel_hue = int((i * 256 / self.num_leds) + self.hue) % 256
            color = self.wheel(pixel_hue)
            self.np[i] = self.scale_color(color, 1.0)
        self.np.write()
        self.hue = (self.hue + 2) % 256  # Advance the rainbow
        
    def solid(self):
        """All LEDs on with solid color"""
        color = self.scale_color(self.solid_color, 1.0)
        for i in range(self.num_leds):
            self.np[i] = color
        self.np.write()
    
    def flashing(self):
        """All LEDs flash on and off"""
        if self.flash_state:
            color = self.scale_color(self.flash_color, 1.0)
            for i in range(self.num_leds):
                self.np[i] = color
        else:
            self.clear()
        self.np.write()
        self.flash_state = not self.flash_state
        
    def pulse(self):
        """All LEDs pulse between min and max brightness"""
        # Calculate scaled color based on pulse brightness
        scale = self.pulse_current / 255
        color = tuple(int(c * scale) for c in self.pulse_color)
        
        for i in range(self.num_leds):
            self.np[i] = color
        self.np.write()
        
        # Update pulse brightness
        self.pulse_current += self.pulse_step * self.pulse_direction
        
        # Reverse direction at boundaries
        if self.pulse_current >= self.pulse_max_brightness:
            self.pulse_current = self.pulse_max_brightness
            self.pulse_direction = -1
        elif self.pulse_current <= self.pulse_min_brightness:
            self.pulse_current = self.pulse_min_brightness
            self.pulse_direction = 1
        
    def update(self):
        """Call this in your main loop - non-blocking"""
        if not self.active:
            return
            
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_update) >= self.update_interval:
            self.last_update = current_time
            
            # Run the appropriate animation
            match self.mode:
                case 'flash':
                    self.flashing()
                case 'pulse':
                    self.pulse()
                case 'chase':
                    self.chase()
                case 'comet':
                    self.comet()
                case 'spinner':
                    self.spinner()
                case 'rainbow_cycle':
                    self.rainbow_cycle()
                case 'solid':
                    self.solid()
                case _:
                    pass

            # Move to next position for rotating animations
            if self.mode in ['chase', 'comet', 'spinner']:
                self.position = (self.position + self.direction) % self.num_leds
            elif self.mode == 'rainbow_cycle':
                # Rainbow also respects direction
                self.hue = (self.hue + (2 * self.direction)) % 256
        
    def pause(self):
        """Pause animation"""
        self.active = False

    def resume(self):
        """Resume animation"""
        self.active = True

    def save_state(self):
        """Save current ring state for later restoration.
        Returns a dict containing all state needed to restore the ring.
        """
        return {
            'mode': self.mode,
            'direction': self.direction,
            'brightness': self.brightness,
            'update_interval': self.update_interval,
            'chase_color': self.chase_color,
            'comet_color': self.comet_color,
            'spinner_colors': self.spinner_colors.copy(),
            'solid_color': self.solid_color,
            'flash_color': self.flash_color,
            'pulse_color': self.pulse_color,
            'pulse_min_brightness': self.pulse_min_brightness,
            'pulse_max_brightness': self.pulse_max_brightness,
            'pulse_step': self.pulse_step,
        }

    def restore_state(self, state):
        """Restore ring state from a previously saved state dict."""
        if not state:
            return
        self.mode = state.get('mode', self.mode)
        self.direction = state.get('direction', self.direction)
        self.brightness = state.get('brightness', self.brightness)
        self.update_interval = state.get('update_interval', self.update_interval)
        self.chase_color = state.get('chase_color', self.chase_color)
        self.comet_color = state.get('comet_color', self.comet_color)
        self.spinner_colors = state.get('spinner_colors', self.spinner_colors)
        self.solid_color = state.get('solid_color', self.solid_color)
        self.flash_color = state.get('flash_color', self.flash_color)
        self.pulse_color = state.get('pulse_color', self.pulse_color)
        self.pulse_min_brightness = state.get('pulse_min_brightness', self.pulse_min_brightness)
        self.pulse_max_brightness = state.get('pulse_max_brightness', self.pulse_max_brightness)
        self.pulse_step = state.get('pulse_step', self.pulse_step)
        # Reset position for clean animation restart
        self.position = 0
