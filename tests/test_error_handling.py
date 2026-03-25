from unittest.mock import PropertyMock

from kelctl.kelerrors import NoModeSetError, ValueOutOfLimitError


def test_setpoint_over_limit(client, mock_device):
    type(mock_device).current = PropertyMock(
        side_effect=ValueOutOfLimitError(50.0, 30.0)
    )
    resp = client.put(
        "/api/v1/setpoint",
        json={"mode": "constant_current", "value": 50.0},
    )
    assert resp.status_code == 400
    assert "50.0" in resp.json()["detail"]
    assert "30.0" in resp.json()["detail"]


def test_setpoint_over_limit_voltage(client, mock_device):
    type(mock_device).voltage = PropertyMock(
        side_effect=ValueOutOfLimitError(200.0, 120.0)
    )
    resp = client.put(
        "/api/v1/setpoint",
        json={"mode": "constant_voltage", "value": 200.0},
    )
    assert resp.status_code == 400
    assert "200.0" in resp.json()["detail"]
    assert "120.0" in resp.json()["detail"]


def test_settings_limit_over_limit(client, mock_device):
    type(mock_device.settings).current_limit = PropertyMock(
        side_effect=ValueOutOfLimitError(999.0, 30.0)
    )
    resp = client.patch(
        "/api/v1/settings",
        json={"current_limit": 999.0},
    )
    assert resp.status_code == 400
    assert "999.0" in resp.json()["detail"]


def test_function_no_mode_set(client, mock_device):
    from kelctl.kelenums import Mode
    type(mock_device).function = PropertyMock(
        side_effect=NoModeSetError(Mode.battery)
    )
    resp = client.put(
        "/api/v1/function",
        json={"function": "constant_voltage"},
    )
    assert resp.status_code == 400
    assert "cannot be set" in resp.json()["detail"]


def test_device_not_connected(client):
    from rnd320_service.device import device_manager
    # Save and override acquire to simulate disconnection
    original = device_manager.acquire

    def fail_acquire():
        raise RuntimeError("Device not connected and reconnection to /dev/ttyACM0 failed")

    device_manager.acquire = fail_acquire
    try:
        resp = client.get("/api/v1/measurements")
        assert resp.status_code == 503
        assert "not connected" in resp.json()["detail"].lower()
    finally:
        device_manager.acquire = original
