"""
OTA (Over-The-Air) Update Handler Module
Manages checking for and applying firmware updates from a remote server
"""

import json
import time
import machine
import os

try:
    import urequests as requests
except ImportError:
    import requests

try:
    from urandom import getrandbits
except ImportError:
    from random import getrandbits


# Configuration
OTA_VERSION_FILE = 'ota_version.json'
OTA_CHECK_MIN_HOURS = 22
OTA_CHECK_MAX_HOURS = 26

# Module state
_ota_config = None
_last_check_time = 0
_next_check_interval = 0


def _get_random_interval():
    """Generate random interval between 22-26 hours in milliseconds."""
    # Random hours between min and max
    range_hours = OTA_CHECK_MAX_HOURS - OTA_CHECK_MIN_HOURS
    random_offset = (getrandbits(16) % (range_hours * 60)) / 60  # Random 0 to range_hours
    hours = OTA_CHECK_MIN_HOURS + random_offset
    return int(hours * 60 * 60 * 1000)  # Convert to milliseconds


def _load_local_version():
    """Load the current local version info."""
    try:
        with open(OTA_VERSION_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'version': '0.0.0', 'files': []}


def _save_local_version(version_info):
    """Save version info after successful update."""
    try:
        with open(OTA_VERSION_FILE, 'w') as f:
            json.dump(version_info, f)
        return True
    except Exception as e:
        print(f'[OTA] Error saving version info: {e}')
        return False


def _compare_versions(local, remote):
    """Compare version strings. Returns True if remote is newer."""
    try:
        local_parts = [int(x) for x in local.split('.')]
        remote_parts = [int(x) for x in remote.split('.')]

        # Pad shorter version with zeros
        while len(local_parts) < len(remote_parts):
            local_parts.append(0)
        while len(remote_parts) < len(local_parts):
            remote_parts.append(0)

        return remote_parts > local_parts
    except:
        return False


def _fetch_remote_manifest(base_url):
    """Fetch the update manifest from the server."""
    try:
        manifest_url = base_url.rstrip('/') + '/manifest.json'
        print(f'[OTA] Fetching manifest from {manifest_url}')

        response = requests.get(manifest_url, timeout=30)
        if response.status_code == 200:
            manifest = response.json()
            response.close()
            return manifest
        else:
            print(f'[OTA] Manifest fetch failed: HTTP {response.status_code}')
            response.close()
            return None
    except Exception as e:
        print(f'[OTA] Error fetching manifest: {e}')
        return None


def _download_file(url, filename):
    """Download a file from URL and save it."""
    try:
        print(f'[OTA] Downloading {filename}...')
        response = requests.get(url, timeout=60)

        if response.status_code == 200:
            # Write to temporary file first
            temp_filename = filename + '.tmp'
            with open(temp_filename, 'w') as f:
                f.write(response.text)
            response.close()

            # Rename temp to actual file
            try:
                os.remove(filename)
            except:
                pass
            os.rename(temp_filename, filename)

            print(f'[OTA] Downloaded {filename} successfully')
            return True
        else:
            print(f'[OTA] Download failed for {filename}: HTTP {response.status_code}')
            response.close()
            return False
    except Exception as e:
        print(f'[OTA] Error downloading {filename}: {e}')
        # Clean up temp file if exists
        try:
            os.remove(filename + '.tmp')
        except:
            pass
        return False


def load_ota_config():
    """Load OTA configuration from config file."""
    global _ota_config
    try:
        with open('ota_config.json', 'r') as f:
            _ota_config = json.load(f)
            return _ota_config
    except:
        # Default config - disabled until configured
        _ota_config = {
            'enabled': False,
            'server_url': '',
            'check_on_boot': True
        }
        return _ota_config


def save_ota_config(config):
    """Save OTA configuration."""
    global _ota_config
    _ota_config = config
    try:
        with open('ota_config.json', 'w') as f:
            json.dump(config, f)
        return True
    except Exception as e:
        print(f'[OTA] Error saving config: {e}')
        return False


def check_for_updates(force=False):
    """Check for available updates.

    Args:
        force: If True, check regardless of interval timing

    Returns:
        dict with 'available', 'current_version', 'new_version', 'files' keys
        or None if check failed or OTA disabled
    """
    global _last_check_time

    config = _ota_config or load_ota_config()

    if not config.get('enabled', False):
        print('[OTA] Updates disabled')
        return None

    server_url = config.get('server_url', '')
    if not server_url:
        print('[OTA] No server URL configured')
        return None

    print('[OTA] Checking for updates...')
    _last_check_time = time.ticks_ms()

    # Fetch remote manifest
    manifest = _fetch_remote_manifest(server_url)
    if not manifest:
        return None

    # Compare versions
    local_info = _load_local_version()
    local_version = local_info.get('version', '0.0.0')
    remote_version = manifest.get('version', '0.0.0')

    update_available = _compare_versions(local_version, remote_version)

    result = {
        'available': update_available,
        'current_version': local_version,
        'new_version': remote_version,
        'files': manifest.get('files', []) if update_available else []
    }

    if update_available:
        print(f'[OTA] Update available: {local_version} -> {remote_version}')
    else:
        print(f'[OTA] Already up to date: {local_version}')

    return result


def apply_update(update_info=None):
    """Download and apply available updates.

    Args:
        update_info: Result from check_for_updates(), or None to check first

    Returns:
        True if update was applied successfully, False otherwise
    """
    config = _ota_config or load_ota_config()

    if not config.get('enabled', False):
        print('[OTA] Updates disabled')
        return False

    # Check for updates if not provided
    if update_info is None:
        update_info = check_for_updates(force=True)

    if not update_info or not update_info.get('available', False):
        print('[OTA] No update available')
        return False

    server_url = config.get('server_url', '').rstrip('/')
    files = update_info.get('files', [])
    new_version = update_info.get('new_version', '0.0.0')

    if not files:
        print('[OTA] No files to update')
        return False

    print(f'[OTA] Applying update to version {new_version}...')

    # Download all files
    success = True
    downloaded_files = []

    for file_info in files:
        if isinstance(file_info, str):
            filename = file_info
        else:
            filename = file_info.get('name', '')

        if not filename:
            continue

        file_url = f'{server_url}/{filename}'
        if _download_file(file_url, filename):
            downloaded_files.append(filename)
        else:
            success = False
            print(f'[OTA] Failed to download {filename}, aborting update')
            break

    if success and downloaded_files:
        # Save new version info
        version_info = {
            'version': new_version,
            'files': downloaded_files,
            'updated_at': time.time()
        }
        _save_local_version(version_info)
        print(f'[OTA] Update complete! Restarting...')
        time.sleep(1)
        machine.reset()

    return success


def init_ota(ring=None):
    """Initialize OTA handler and check for updates on boot if enabled.

    Args:
        ring: Optional LEDRing instance for visual feedback

    Returns:
        Random interval in ms for next check
    """
    global _next_check_interval, _last_check_time

    config = load_ota_config()
    _last_check_time = time.ticks_ms()
    _next_check_interval = _get_random_interval()

    hours = _next_check_interval / (1000 * 60 * 60)
    print(f'[OTA] Initialized. Next check in {hours:.1f} hours')

    # Check on boot if enabled
    if config.get('enabled', False) and config.get('check_on_boot', True):
        print('[OTA] Boot check enabled, checking for updates...')

        # Visual feedback if ring available
        if ring:
            ring.set_mode('pulse')
            ring.set_pulse_color('cyan')

        update_info = check_for_updates(force=True)

        if update_info and update_info.get('available', False):
            # Auto-apply update
            if config.get('auto_update', True):
                apply_update(update_info)
            else:
                print('[OTA] Update available but auto_update is disabled')

        # Restore ring mode
        if ring:
            ring.set_mode('chase')
            ring.set_chase_color('green')

    return _next_check_interval


def should_check_now():
    """Check if it's time for a periodic update check.

    Returns:
        True if enough time has passed since last check
    """
    global _last_check_time, _next_check_interval

    if _next_check_interval == 0:
        _next_check_interval = _get_random_interval()

    current_time = time.ticks_ms()
    elapsed = time.ticks_diff(current_time, _last_check_time)

    return elapsed >= _next_check_interval


def periodic_check():
    """Perform periodic update check if interval has elapsed.

    Call this from the main loop. It will only check when the
    random interval (22-26 hours) has elapsed.

    Returns:
        True if an update was applied (device will reset),
        False otherwise
    """
    global _last_check_time, _next_check_interval

    if not should_check_now():
        return False

    config = _ota_config or load_ota_config()
    if not config.get('enabled', False):
        # Reset timer even if disabled to prevent immediate check if re-enabled
        _last_check_time = time.ticks_ms()
        _next_check_interval = _get_random_interval()
        return False

    print('[OTA] Periodic check triggered')
    update_info = check_for_updates(force=True)

    # Generate new random interval for next check
    _next_check_interval = _get_random_interval()
    _last_check_time = time.ticks_ms()

    hours = _next_check_interval / (1000 * 60 * 60)
    print(f'[OTA] Next check in {hours:.1f} hours')

    if update_info and update_info.get('available', False):
        if config.get('auto_update', True):
            return apply_update(update_info)

    return False


def get_current_version():
    """Get the current installed version."""
    info = _load_local_version()
    return info.get('version', '0.0.0')


def get_ota_status():
    """Get current OTA status for diagnostics."""
    global _last_check_time, _next_check_interval

    config = _ota_config or load_ota_config()
    current_time = time.ticks_ms()
    elapsed = time.ticks_diff(current_time, _last_check_time)
    remaining = max(0, _next_check_interval - elapsed)

    return {
        'enabled': config.get('enabled', False),
        'server_url': config.get('server_url', ''),
        'current_version': get_current_version(),
        'last_check_ms_ago': elapsed,
        'next_check_in_ms': remaining,
        'next_check_in_hours': remaining / (1000 * 60 * 60)
    }
