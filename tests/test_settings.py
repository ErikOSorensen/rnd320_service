def test_get_settings(client):
    resp = client.get("/api/v1/settings")
    assert resp.status_code == 200
    data = resp.json()
    assert data["voltage_limit"] == 120.0
    assert data["current_limit"] == 30.0
    assert data["power_limit"] == 300.0
    assert data["resistance_limit"] == 9999.0
    assert data["beep"] == "ON"
    assert data["lock"] == "OFF"


def test_patch_settings_limits(client, mock_device):
    resp = client.patch(
        "/api/v1/settings",
        json={"current_limit": 20.0},
    )
    assert resp.status_code == 200


def test_patch_settings_toggle_on(client, mock_device):
    resp = client.patch(
        "/api/v1/settings",
        json={"beep": "OFF"},
    )
    assert resp.status_code == 200
    mock_device.settings.beep.off.assert_called_once()


def test_patch_settings_toggle_off(client, mock_device):
    resp = client.patch(
        "/api/v1/settings",
        json={"lock": "ON"},
    )
    assert resp.status_code == 200
    mock_device.settings.lock.on.assert_called_once()


def test_patch_settings_empty(client):
    resp = client.patch("/api/v1/settings", json={})
    assert resp.status_code == 200
