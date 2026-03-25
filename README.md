# rnd320-service

REST API service for controlling an RND320 / Korad KEL103 electronic DC load over USB serial.

Built with [FastAPI](https://fastapi.tiangolo.com/) and [py-kelctl](https://github.com/vorbeiei/kelctl). Designed to run on a Raspberry Pi as a systemd service.

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
- RND320 / KEL103 connected via USB

## Quick Start

```bash
# Clone and install
git clone <repo-url>
cd rnd320_service
uv sync

# Run (device must be connected)
uv run rnd320-service
```

The service starts on `http://0.0.0.0:8320` by default. Interactive API docs are available at `http://<host>:8320/docs`.

## Configuration

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

## API Reference

All endpoints are under `/api/v1/`. Full interactive documentation (Swagger UI) is served at `/docs` and the OpenAPI schema at `/openapi.json`.

### Health

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness check. Returns `{"status": "ok", "device_connected": true/false}` |

### Device Info

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/device` | Model string, device status, and network info |

### Measurements

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/measurements` | Read measured voltage (V), current (A), and power (W) |

Example response:
```json
{"voltage": 12.05, "current": 1.503, "power": 18.12}
```

### Input Control

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/input` | Get current input state |
| PUT | `/api/v1/input` | Enable or disable the load input |

Example request:
```json
{"state": "ON"}
```

### Setpoint

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

### Function / Mode

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/function` | Get the current operating mode |
| PUT | `/api/v1/function` | Set the operating mode directly |

Example request:
```json
{"function": "constant_voltage"}
```

### Settings

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

### Battery Test

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

## Raspberry Pi Deployment

### 1. Install uv and the service

```bash
# Install uv (if not already present)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repo and install
cd /opt
sudo git clone <repo-url> rnd320-service
cd rnd320-service
sudo uv sync
```

### 2. Create a service user

```bash
sudo useradd -r -s /sbin/nologin -G dialout rnd320
```

The `dialout` group grants access to serial ports.

### 3. Configure the environment

```bash
sudo cp rnd320-service.env.example /etc/rnd320-service.env
sudo nano /etc/rnd320-service.env
```

### 4. Install and enable the systemd service

Update `ExecStart` in the service file to match the installed path:

```bash
# Edit the service file if needed
sudo cp rnd320-service.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now rnd320-service
```

### 5. Verify

```bash
sudo systemctl status rnd320-service
curl http://localhost:8320/health
```

### USB Device Permissions

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

### Disable USB Autosuspend

Linux power management can suspend idle USB devices, which kills the serial connection. This is a common cause of the service losing contact with the device after a period of inactivity. Disable autosuspend for USB devices:

```bash
# /etc/udev/rules.d/99-rnd320.rules (add to the existing rule file)
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="0416", ATTR{idProduct}=="5011", ATTR{power/autosuspend}="-1"
```

Alternatively, disable USB autosuspend globally via a kernel parameter. Add `usbcore.autosuspend=-1` to `/boot/cmdline.txt` (Raspberry Pi OS) or `/boot/firmware/cmdline.txt` (Ubuntu):

```
... rootwait usbcore.autosuspend=-1
```

### Static IP Address

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

### Reducing SD Card Wear

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

### Firewall

If the Pi is on a shared network, restrict access to the service port:

```bash
sudo apt install ufw
sudo ufw default deny incoming
sudo ufw allow ssh
sudo ufw allow 8320/tcp
sudo ufw enable
```

### Recommended OS

Raspberry Pi OS Lite (64-bit) is a good baseline — no desktop overhead, well-supported on Pi 3B. For an even leaner setup, DietPi or Alpine Linux are options, though they require more manual configuration.

## Development

```bash
# Install dependencies
uv sync

# Run the service locally
uv run rnd320-service

# Open the interactive API docs
# http://localhost:8320/docs
```

## License

MIT
