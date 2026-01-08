"""
Web Server Module
Handles captive portal, DNS server, and configuration web interface
"""

import socket
from constants import DNS_PORT
from config_manager import save_config, save_mqtt_config
from ota_handler import save_ota_config


def setup_dns_server():
    """Setup DNS server for captive portal (non-blocking)"""
    try:
        dns_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        dns_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        dns_socket.bind(('0.0.0.0', DNS_PORT))
        dns_socket.setblocking(False)
        print('DNS server started on port 53')
        return dns_socket
    except Exception as e:
        print(f'DNS server setup failed: {e}')
        return None


def handle_dns_request(dns_socket, ap_ip):
    """Handle DNS requests - redirect all domains to AP IP"""
    try:
        data, addr = dns_socket.recvfrom(512)
        
        # Parse DNS query
        transaction_id = data[0:2]
        flags = b'\x81\x80'  # Standard query response, no error
        questions = data[4:6]
        answer_rrs = b'\x00\x01'  # One answer
        authority_rrs = b'\x00\x00'
        additional_rrs = b'\x00\x00'
        
        # Extract domain name from query (we don't actually need to parse it)
        # Just respond with our AP IP for ANY domain
        
        # DNS Answer section
        # Pointer to domain name in question
        answer_name = b'\xc0\x0c'
        # Type A (host address)
        answer_type = b'\x00\x01'
        # Class IN
        answer_class = b'\x00\x01'
        # TTL (1 minute)
        answer_ttl = b'\x00\x00\x00\x3c'
        # Data length (4 bytes for IPv4)
        answer_length = b'\x00\x04'
        # IP address (AP IP converted to bytes)
        ip_parts = ap_ip.split('.')
        answer_data = bytes([int(ip_parts[0]), int(ip_parts[1]), int(ip_parts[2]), int(ip_parts[3])])
        
        # Construct DNS response
        dns_response = (
            transaction_id + flags + questions + answer_rrs + 
            authority_rrs + additional_rrs + data[12:] + 
            answer_name + answer_type + answer_class + 
            answer_ttl + answer_length + answer_data
        )
        
        # Send response
        dns_socket.sendto(dns_response, addr)
        
    except OSError:
        # No data available, this is normal for non-blocking
        pass
    except Exception as e:
        print(f'DNS error: {e}')


def web_page():
    """Generate configuration web page"""
    html = """<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>ESP32 WiFi Setup</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 500px;
            margin: 30px auto;
            padding: 20px;
            background: #f0f0f0;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 10px;
        }
        h2 {
            color: #555;
            font-size: 18px;
            margin-top: 20px;
            margin-bottom: 10px;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 5px;
        }
        input {
            width: 100%;
            padding: 12px;
            margin: 8px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
            box-sizing: border-box;
        }
        button {
            width: 100%;
            padding: 12px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin-top: 10px;
        }
        button:hover {
            background: #45a049;
        }
        .info {
            color: #666;
            font-size: 13px;
            margin-top: 10px;
        }
        label {
            color: #555;
            font-size: 14px;
            display: block;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>ESP32 Configuration</h1>
        <form action="/configure" method="POST">
            <h2>WiFi Settings</h2>
            <label>Network SSID *</label>
            <input type="text" name="ssid" placeholder="Your WiFi Network" required>
            
            <label>Network Password *</label>
            <input type="password" name="password" placeholder="WiFi Password" required>
            
            <h2>MQTT Settings</h2>
            <label>MQTT Broker</label>
            <input type="text" name="broker" placeholder="broker.hivemq.com" value="broker.hivemq.com">
            
            <label>MQTT Port</label>
            <input type="number" name="port" placeholder="1883" value="1883">
            
            <label>MQTT Topic</label>
            <input type="text" name="topic" placeholder="esp32/test" value="esp32/test">
            
            <label>MQTT Username (optional)</label>
            <input type="text" name="mqtt_user" placeholder="Leave blank if not required">
            
            <label>MQTT Password (optional)</label>
            <input type="password" name="mqtt_pass" placeholder="Leave blank if not required">

            <h2>OTA Update Settings</h2>
            <label>
                <input type="checkbox" name="ota_enabled" value="1" style="width: auto; margin-right: 8px;">
                Enable OTA Updates
            </label>

            <label>OTA Server URL</label>
            <input type="text" name="ota_url" placeholder="http://your-server.com/firmware">

            <label>
                <input type="checkbox" name="ota_boot_check" value="1" checked style="width: auto; margin-right: 8px;">
                Check for updates on boot
            </label>

            <label>
                <input type="checkbox" name="ota_auto_update" value="1" checked style="width: auto; margin-right: 8px;">
                Automatically apply updates
            </label>

            <button type="submit">Save & Connect</button>
        </form>
        <div class="info">
            * Required fields. MQTT and OTA settings are optional.
    </div>
</body>
</html>"""
    return html


def success_page():
    """Generate success page"""
    html = """<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Configuration Saved</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 400px;
            margin: 50px auto;
            padding: 20px;
            text-align: center;
        }
        .success {
            color: #4CAF50;
            font-size: 24px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <h1>✓ Configuration Saved</h1>
    <p class="success">ESP32 will now restart, connect to WiFi, and establish MQTT connection.</p>
    <p>You can close this page.</p>
</body>
</html>"""
    return html


def parse_post_data(data):
    """Parse POST form data"""
    params = {}
    try:
        data_str = data.decode('utf-8')
        pairs = data_str.split('&')
        for pair in pairs:
            if '=' in pair:
                key, value = pair.split('=', 1)
                # URL decode
                value = value.replace('+', ' ')
                value = value.replace('%40', '@')
                value = value.replace('%2F', '/')
                value = value.replace('%3A', ':')
                value = value.replace('%23', '#')
                params[key] = value
    except:
        pass
    return params


def setup_web_server():
    """Setup web server socket (non-blocking)"""
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    s.setblocking(False)  # Make socket non-blocking
    print('Web server running on http://192.168.4.1')
    return s


def handle_web_request(server_socket):
    """Handle web requests in non-blocking mode. Returns True if config received."""
    try:
        cl, addr = server_socket.accept()
        cl.setblocking(True)  # Make client socket blocking for easier handling
        print('Client connected from', addr)
        
        try:
            request = cl.recv(1024)
            request_str = request.decode('utf-8')
            
            # Check if this is a captive portal detection request
            is_captive_portal_check = any(detect in request_str for detect in [
                'generate_204',  # Android
                'hotspot-detect.html',  # iOS/macOS
                'connecttest.txt',  # Windows
                'success.txt',  # Windows
                'ncsi.txt',  # Windows
                'connecttest',  # General
            ])
            
            if 'POST /configure' in request_str:
                # Extract POST data
                parts = request_str.split('\r\n\r\n')
                if len(parts) > 1:
                    post_data = parts[1]
                    params = parse_post_data(post_data.encode())
                    
                    if 'ssid' in params and 'password' in params:
                        ssid = params['ssid']
                        password = params['password']
                        
                        # Save WiFi config
                        print(f'Received WiFi credentials - SSID: {ssid}')
                        save_config(ssid, password)
                        
                        # Save MQTT config
                        broker = params.get('broker', 'broker.hivemq.com')
                        port = int(params.get('port', '1883'))
                        topic = params.get('topic', 'esp32/test')
                        mqtt_user = params.get('mqtt_user', '')
                        mqtt_pass = params.get('mqtt_pass', '')

                        print(f'Received MQTT config - Broker: {broker}:{port}')
                        save_mqtt_config(broker, port, topic, mqtt_user, mqtt_pass)

                        # Save OTA config
                        ota_config = {
                            'enabled': 'ota_enabled' in params,
                            'server_url': params.get('ota_url', ''),
                            'check_on_boot': 'ota_boot_check' in params,
                            'auto_update': 'ota_auto_update' in params
                        }
                        print(f'Received OTA config - Enabled: {ota_config["enabled"]}, URL: {ota_config["server_url"]}')
                        save_ota_config(ota_config)

                        response = 'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n'
                        response += success_page()
                        cl.send(response)
                        cl.close()
                        
                        return True  # Signal that configuration was received
            elif is_captive_portal_check:
                # Redirect captive portal detection to our configuration page
                print('Captive portal detection - redirecting to config page')
                response = 'HTTP/1.1 302 Found\r\n'
                response += 'Location: http://192.168.4.1/\r\n'
                response += 'Content-Length: 0\r\n'
                response += '\r\n'
                cl.send(response)
            else:
                # Serve configuration page for all other requests
                response = 'HTTP/1.1 200 OK\r\n'
                response += 'Content-Type: text/html\r\n'
                response += 'Cache-Control: no-cache, no-store, must-revalidate\r\n'
                response += '\r\n'
                response += web_page()
                cl.send(response)
        except Exception as e:
            print('Request handling error:', e)
        finally:
            cl.close()
            
    except OSError as e:
        # No connection available (EAGAIN), this is normal for non-blocking
        pass
    except Exception as e:
        print('Socket error:', e)
    
    return False
