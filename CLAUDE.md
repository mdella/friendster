# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Friendster is a modular MicroPython application for the ESP32-C3 microcontroller that controls a WS2812 RGB LED ring (24 LEDs) with WiFi connectivity, MQTT integration, and web-based captive portal configuration.

**Platform:** ESP32-C3 running MicroPython (no build system - interpreted code)

## Development Workflow

### Deployment

Upload all `.py` files to ESP32 flash storage using:
- **Thonny IDE** - MicroPython IDE with built-in ESP32 support
- **ampy** - `ampy --port /dev/ttyUSB0 put filename.py`
- **rshell** - `rshell -p /dev/ttyUSB0 cp filename.py /pyboard/`

Device automatically executes `main.py` on boot.

### Testing & Debugging

No automated test framework. Debug via:
- REPL serial connection for interactive testing
- Print statements throughout code log to serial console
- Import individual modules in REPL: `from led_ring import LEDRing`

## Architecture

### Module Responsibilities

| Module | Purpose |
|--------|---------|
| `main.py` | Orchestrator - initializes modules, runs main event loop |
| `constants.py` | Centralized configuration (GPIO pins, timing, colors, MQTT settings) |
| `led_ring.py` | LEDRing class - 7 animation modes (chase, comet, spinner, rainbow_cycle, solid, flash, pulse) |
| `button_handler.py` | Debounced button input with short/long/very-long press detection |
| `config_manager.py` | JSON persistence layer for WiFi and MQTT configs |
| `mqtt_handler.py` | MQTT client, callbacks, and LED ring command handlers |
| `ota_handler.py` | OTA updates - checks on boot and every 22-26 hours (randomized) |
| `wifi_manager.py` | WiFi STA connection and AP mode for setup |
| `web_server.py` | HTTP server + DNS for captive portal configuration |

### Key Design Patterns

1. **Non-blocking I/O** - All operations (LED updates, button checks, MQTT polling, web requests) are non-blocking interval-based to prevent main loop stalls

2. **Configuration Flow** - JSON files (`wifi_config.json`, `mqtt_config.json`) persist settings. Web form during AP mode writes configs, then triggers `machine.reset()`

3. **Hardware Pins** - GPIO 8: LED Ring, GPIO 5: Button (pull-up enabled)

### Application Flow

**Normal operation:** Load WiFi config → Connect (3 retries) → OTA check on boot → Load MQTT config → Connect to broker → Main loop (LED updates, button checks, MQTT polling, 60s heartbeat, OTA periodic check)

**Setup mode (no WiFi config or connection fails):** Start AP mode ("ESP32-Setup" / "12345678") → Cyan chase animation → DNS + HTTP servers → Serve captive portal → Save config on form submit → Reset

## MQTT Topics

**Subscribed (LED control):**
- `{topic}/ring/chase` - Chase animation
- `{topic}/ring/static` - Solid color
- `{topic}/ring/flash` - Flashing animation
- `{topic}/ring/comet` - Comet with tail
- `{topic}/ring/spinner` - Multi-arm spinner
- `{topic}/ring/rainbow` - Rainbow cycle
- `{topic}/ring/pulse` - Pulsing brightness
- `{topic}/ring/reset` - Reset to default

**Subscribed (OTA control):**
- `{topic}/ota/check` - Trigger update check
- `{topic}/ota/update` - Apply available update
- `{topic}/ota/status` - Request OTA status

**Published (events):** `{topic}/heartbeat`, `{topic}/button/1`, `{topic}/button/2`, `{topic}/button/3`

**Published (OTA responses):** `{topic}/ota/check/response`, `{topic}/ota/update/response`, `{topic}/ota/status/response`

**Payload formats:**
- Simple: `"red"` (color name)
- JSON: `{"color": "red", "speed": 30, "brightness": 100, "direction": "cw"}`
- Spinner: `{"colors": ["red", "green", "blue"]}`
- Pulse: `{"color": "blue", "min": 10, "max": 255, "step": 5}`

## OTA Updates

OTA is configured via `ota_config.json`:
```json
{"enabled": true, "server_url": "http://example.com/firmware", "check_on_boot": true, "auto_update": true}
```

**Server manifest format** (`manifest.json`):
```json
{"version": "1.0.0", "files": ["main.py", "led_ring.py", "mqtt_handler.py"]}
```

**Check timing:** Randomized 22-26 hour interval to prevent server load spikes from many devices.
