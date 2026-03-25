from unittest.mock import PropertyMock

from kelctl.kelenums import Mode, OnOffState


def test_get_battery_config(client):
    resp = client.get("/api/v1/battery/config/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["save_slot"] == 1
    assert data["current_range"] == 30.0
    assert data["discharge_current"] == 1.0
    assert data["cutoff_voltage"] == 3.0


def test_get_battery_config_invalid_slot(client):
    resp = client.get("/api/v1/battery/config/0")
    assert resp.status_code == 400

    resp = client.get("/api/v1/battery/config/11")
    assert resp.status_code == 400


def test_set_battery_config(client, mock_device):
    resp = client.put(
        "/api/v1/battery/config",
        json={
            "save_slot": 2,
            "current_range": 30.0,
            "discharge_current": 2.0,
            "cutoff_voltage": 2.8,
            "cutoff_capacity": 50.0,
            "cutoff_time": 300.0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["save_slot"] == 2
    assert data["discharge_current"] == 2.0
    mock_device.set_batt.assert_called_once()


def test_set_battery_config_invalid_slot(client):
    resp = client.put(
        "/api/v1/battery/config",
        json={
            "save_slot": 11,
            "current_range": 30.0,
            "discharge_current": 1.0,
            "cutoff_voltage": 3.0,
            "cutoff_capacity": 100.0,
            "cutoff_time": 600.0,
        },
    )
    assert resp.status_code == 400


def test_recall_battery_config(client, mock_device):
    resp = client.post("/api/v1/battery/recall/1")
    assert resp.status_code == 200
    mock_device.recall_batt.assert_called_once_with(1)


def test_recall_battery_config_invalid_slot(client):
    resp = client.post("/api/v1/battery/recall/0")
    assert resp.status_code == 400


def test_battery_status_running(client, mock_device):
    mock_device.input.get.return_value = OnOffState("ON")
    type(mock_device).function = PropertyMock(return_value=Mode.battery)

    resp = client.get("/api/v1/battery/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["capacity"] == 1.234
    assert data["time"] == 45.2
    assert data["input"] == "ON"
    assert data["function"] == "BATTERY"
    assert data["running"] is True


def test_battery_status_not_running(client, mock_device):
    mock_device.input.get.return_value = OnOffState("OFF")
    type(mock_device).function = PropertyMock(return_value=Mode.battery)

    resp = client.get("/api/v1/battery/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["running"] is False
