# rnd320-service

REST API service for controlling an RND320 / Korad KEL103 electronic DC load over USB serial.

Built with [FastAPI](https://fastapi.tiangolo.com/) and [py-kelctl](https://github.com/vorbeiei/kelctl). Designed to run on a Raspberry Pi as a systemd service.

## Table of Contents

1. [Requirements](#1-requirements)
2. [Quick Start](#2-quick-start)
3. [Configuration](#3-configuration)
4. [API Reference](#4-api-reference)
   - [4.1 Health](#41-health)
   - [4.2 Device Info](#42-device-info)
   - [4.3 Measurements](#43-measurements)
   - [4.4 Input Control](#44-input-control)
   - [4.5 Setpoint](#45-setpoint)
   - [4.6 Function / Mode](#46-function--mode)
   - [4.7 Settings](#47-settings)
   - [4.8 Battery Test](#48-battery-test)
5. [MQTT Telemetry](#5-mqtt-telemetry)
6. [Raspberry Pi Deployment](#6-raspberry-pi-deployment)
   - [6.1 Install uv and the service](#61-install-uv-and-the-service)
   - [6.2 Create a service user](#62-create-a-service-user)
   - [6.3 Configure the environment](#63-configure-the-environment)
   - [6.4 Install and enable the systemd service](#64-install-and-enable-the-systemd-service)
   - [6.5 Verify](#65-verify)
   - [6.6 USB Device Permissions](#66-usb-device-permissions)
   - [6.7 Disable USB Autosuspend](#67-disable-usb-autosuspend)
   - [6.8 Static IP Address](#68-static-ip-address)
   - [6.9 Reducing SD Card Wear](#69-reducing-sd-card-wear)
   - [6.10 Firewall](#610-firewall)
   - [6.11 Recommended OS](#611-recommended-os)
7. [Development](#7-development)
8. [License](#8-license)

## 1. Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
- RND320 / KEL103 connected via USB

## 2. Quick Start

```bash
# Clone and install
git clone <repo-url>
cd rnd320_service
uv sync

# Run (device must be connected)
uv run rnd320-service
```

The service starts on `http://0.0.0.0:8320` by default. Interactive API docs are available at `http://<host>:8320/docs`.

## 3. Configuration

All configuration is done via environment variables:

| Variable | Default | Description |
|---|---|---|
| `RND320_PORT` | `/dev/ttyACM0` | Serial port path for the DC load |
| `RND320_BAUDRATE` | `115200` | Serial baud rate |
| `RND320_HOST` | `0.0.0.0` | HTTP bind address |
| `RND320_HTTP_PORT` | `8320` | HTTP port |

You can set these inline, export them, or use the systemd environment file (see below).

```bash
# Example: run on a different port with a specific serial device
RND320_PORT=/dev/ttyUSB0 RND320_HTTP_PORT=9000 uv run rnd320-service
```

## 4. API Reference

All endpoints are under `/api/v1/`. Full interactive documentation (Swagger UI) is served at `/docs` and the OpenAPI schema at `/openapi.json`.

### 4.1 Health

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness check. Returns `{"status": "ok", "device_connected": true/false}` |

### 4.2 Device Info

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/device` | Model string, device status, and network info |

### 4.3 Measurements

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/measurements` | Read measured voltage (V), current (A), and power (W) |

Example response:
```json
{"voltage": 12.05, "current": 1.503, "power": 18.12}
```

### 4.4 Input Control

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/input` | Get current input state |
| PUT | `/api/v1/input` | Enable or disable the load input |

Example request:
```json
{"state": "ON"}
```

### 4.5 Setpoint

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/setpoint` | Get current mode and all setpoint values |
| PUT | `/api/v1/setpoint` | Set mode and value (switches the load to the corresponding constant mode) |

Example — set constant current to 2.0 A:
```json
{"mode": "constant_current", "value": 2.0}
```

Available modes: `constant_voltage`, `constant_current`, `constant_resistance`, `constant_power`, `short`.

Example response:
```json
{"mode": "CC", "voltage": 12.0, "current": 2.0, "power": 24.0, "resistance": 6.0}
```

### 4.6 Function / Mode

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/function` | Get the current operating mode |
| PUT | `/api/v1/function` | Set the operating mode directly |

Example request:
```json
{"function": "constant_voltage"}
```

### 4.7 Settings

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/settings` | Get limits and toggle settings |
| PATCH | `/api/v1/settings` | Update settings (partial — only include fields to change) |

Example — set current limit and enable beep:
```json
{"current_limit": 30.0, "beep": "ON"}
```

Settings fields:
- **Limits**: `voltage_limit`, `current_limit`, `power_limit`, `resistance_limit`
- **Toggles** (`"ON"` / `"OFF"`): `beep`, `lock`, `dhcp`, `trigger`, `compensation`

### 4.8 Battery Test

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/battery/config/{slot}` | Get battery test config from slot (1-10) |
| PUT | `/api/v1/battery/config` | Configure and activate a battery test |
| POST | `/api/v1/battery/recall/{slot}` | Recall a previously saved battery test config |
| GET | `/api/v1/battery/status` | Get test progress: capacity, time, and whether the test is still running |

Example — configure a battery discharge test:
```json
{
  "save_slot": 1,
  "current_range": 30.0,
  "discharge_current": 1.0,
  "cutoff_voltage": 3.0,
  "cutoff_capacity": 100.0,
  "cutoff_time": 600.0
}
```

Example status response (test in progress):
```json
{"capacity": 1.234, "time": 45.2, "input": "ON", "function": "BATTERY", "running": true}
```

When the device reaches a cutoff condition it turns off the input and `running` becomes `false`.

## 5. MQTT Telemetry

The service can optionally publish measurements to an MQTT broker. This is useful for logging, dashboards (e.g. Grafana via Telegraf), or integration with home automation systems. MQTT keeps telemetry decoupled from the REST API — any number of subscribers can independently log, visualize, or alert on the data.

### 5.1 Installation

MQTT support is an optional dependency:

```bash
uv sync --extra mqtt
```

### 5.2 Configuration

Set `RND320_MQTT_BROKER` to enable publishing. All other MQTT settings have sensible defaults:

| Variable | Default | Description |
|---|---|---|
| `RND320_MQTT_BROKER` | *(unset — disabled)* | MQTT broker hostname or IP |
| `RND320_MQTT_PORT` | `1883` | MQTT broker port |
| `RND320_MQTT_TOPIC` | `rnd320/measurements` | Topic to publish to |
| `RND320_MQTT_INTERVAL` | `1.0` | Publish interval in seconds |
| `RND320_MQTT_USERNAME` | *(unset)* | Broker username (optional) |
| `RND320_MQTT_PASSWORD` | *(unset)* | Broker password (optional) |

### 5.3 Behavior

- Publishing only occurs when the **load input is ON**. When the input is off, no messages are sent.
- Each message is a JSON payload on the configured topic:

```json
{
  "timestamp": "2026-03-25T14:30:00.123456+00:00",
  "voltage": 12.05,
  "current": 1.503,
  "power": 18.12
}
```

- The `timestamp` is the UTC time when the measurement was taken. Subscribers can use this or their own receive time depending on accuracy needs.
- If the MQTT broker is unreachable at startup, the service logs an error and continues running — the REST API is unaffected.
- If the broker connection is lost after startup, the publisher reconnects automatically with exponential backoff (1s to 60s). No service restart is needed.

### 5.4 Example: subscribing with mosquitto

```bash
mosquitto_sub -h localhost -t rnd320/measurements
```

## 6. Raspberry Pi Deployment

### 6.1 Install uv and the service

```bash
# Install uv (if not already present)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repo and install
cd /opt
sudo git clone <repo-url> rnd320-service
cd rnd320-service
sudo uv sync
```

### 6.2 Create a service user

```bash
sudo useradd -r -s /sbin/nologin -G dialout rnd320
```

The `dialout` group grants access to serial ports.

### 6.3 Configure the environment

```bash
sudo cp rnd320-service.env.example /etc/rnd320-service.env
sudo nano /etc/rnd320-service.env
```

### 6.4 Install and enable the systemd service

Update `ExecStart` in the service file to match the installed path:

```bash
# Edit the service file if needed
sudo cp rnd320-service.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now rnd320-service
```

### 6.5 Verify

```bash
sudo systemctl status rnd320-service
curl http://localhost:8320/health
```

### 6.6 USB Device Permissions

If the service cannot open the serial port, ensure the device node is accessible. You can add a udev rule for consistent naming:

```bash
# /etc/udev/rules.d/99-rnd320.rules
SUBSYSTEM=="tty", ATTRS{idVendor}=="0416", ATTRS{idProduct}=="5011", SYMLINK+="rnd320", GROUP="dialout", MODE="0660"
```

Then reload udev:
```bash
sudo udevadm control --reload-rules && sudo udevadm trigger
```

Set `RND320_PORT=/dev/rnd320` in your environment file to use the stable symlink.

### 6.7 Disable USB Autosuspend

Linux power management can suspend idle USB devices, which kills the serial connection. This is a common cause of the service losing contact with the device after a period of inactivity. Disable autosuspend for USB devices:

```bash
# /etc/udev/rules.d/99-rnd320.rules (add to the existing rule file)
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="0416", ATTR{idProduct}=="5011", ATTR{power/autosuspend}="-1"
```

Alternatively, disable USB autosuspend globally via a kernel parameter. Add `usbcore.autosuspend=-1` to `/boot/cmdline.txt` (Raspberry Pi OS) or `/boot/firmware/cmdline.txt` (Ubuntu):

```
... rootwait usbcore.autosuspend=-1
```

### 6.8 Static IP Address

A service that other machines need to reach should have a predictable address. With NetworkManager (default on recent Raspberry Pi OS):

```bash
sudo nmcli con mod "Wired connection 1" \
  ipv4.method manual \
  ipv4.addresses 192.168.1.50/24 \
  ipv4.gateway 192.168.1.1 \
  ipv4.dns "192.168.1.1"
sudo nmcli con up "Wired connection 1"
```

With `dhcpcd` (older Raspberry Pi OS), add to `/etc/dhcpcd.conf`:

```
interface eth0
static ip_address=192.168.1.50/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1
```

### 6.9 Reducing SD Card Wear

A headless Pi running 24/7 can wear out an SD card through constant log writes. A few mitigations:

```bash
# Mount /tmp and /var/log as tmpfs (RAM-backed)
# Add to /etc/fstab:
tmpfs /tmp     tmpfs defaults,noatime,nosuid,nodev,size=64M 0 0
tmpfs /var/log tmpfs defaults,noatime,nosuid,nodev,size=32M 0 0
```

Note: mounting `/var/log` as tmpfs means logs are lost on reboot. If you need persistent logs, configure log rotation instead:

```bash
# /etc/logrotate.d/rnd320-service
/var/log/rnd320-service/*.log {
    daily
    rotate 3
    compress
    missingok
    notifempty
    maxsize 10M
}
```

You can also reduce journal disk usage:

```bash
sudo journalctl --vacuum-size=50M
# Make it permanent in /etc/systemd/journald.conf:
# SystemMaxUse=50M
```

### 6.10 Firewall

If the Pi is on a shared network, restrict access to the service port:

```bash
sudo apt install ufw
sudo ufw default deny incoming
sudo ufw allow ssh
sudo ufw allow 8320/tcp
sudo ufw enable
```

### 6.11 Recommended OS

Raspberry Pi OS Lite (64-bit) is a good baseline — no desktop overhead, well-supported on Pi 3B. For an even leaner setup, DietPi or Alpine Linux are options, though they require more manual configuration.

## 7. Development

```bash
# Install dependencies
uv sync

# Run the service locally
uv run rnd320-service

# Open the interactive API docs
# http://localhost:8320/docs

# Run tests (no hardware required — uses a mocked device)
uv run pytest tests/ -v
```

## 8. License

MIT
