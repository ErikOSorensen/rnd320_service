def test_get_input(client):
    resp = client.get("/api/v1/input")
    assert resp.status_code == 200
    assert resp.json()["state"] == "OFF"


def test_set_input_on(client, mock_device):
    resp = client.put("/api/v1/input", json={"state": "ON"})
    assert resp.status_code == 200
    mock_device.input.on.assert_called_once()


def test_set_input_off(client, mock_device):
    resp = client.put("/api/v1/input", json={"state": "OFF"})
    assert resp.status_code == 200
    mock_device.input.off.assert_called_once()


def test_set_input_invalid(client):
    resp = client.put("/api/v1/input", json={"state": "MAYBE"})
    assert resp.status_code == 400


def test_set_input_case_insensitive(client, mock_device):
    resp = client.put("/api/v1/input", json={"state": "on"})
    assert resp.status_code == 200
    mock_device.input.on.assert_called_once()


def test_get_setpoint(client):
    resp = client.get("/api/v1/setpoint")
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "CC"
    assert data["voltage"] == 12.0
    assert data["current"] == 2.0
    assert data["power"] == 24.0
    assert data["resistance"] == 6.0


def test_set_setpoint_constant_current(client, mock_device):
    resp = client.put(
        "/api/v1/setpoint",
        json={"mode": "constant_current", "value": 3.0},
    )
    assert resp.status_code == 200
    mock_device.current  # property was set via setter


def test_set_setpoint_constant_voltage(client, mock_device):
    resp = client.put(
        "/api/v1/setpoint",
        json={"mode": "constant_voltage", "value": 5.0},
    )
    assert resp.status_code == 200


def test_set_setpoint_constant_resistance(client, mock_device):
    resp = client.put(
        "/api/v1/setpoint",
        json={"mode": "constant_resistance", "value": 10.0},
    )
    assert resp.status_code == 200


def test_set_setpoint_constant_power(client, mock_device):
    resp = client.put(
        "/api/v1/setpoint",
        json={"mode": "constant_power", "value": 50.0},
    )
    assert resp.status_code == 200


def test_set_setpoint_short(client, mock_device):
    resp = client.put(
        "/api/v1/setpoint",
        json={"mode": "short", "value": 0},
    )
    assert resp.status_code == 200


def test_set_setpoint_invalid_mode(client):
    resp = client.put(
        "/api/v1/setpoint",
        json={"mode": "invalid", "value": 1.0},
    )
    assert resp.status_code == 422


def test_get_function(client):
    resp = client.get("/api/v1/function")
    assert resp.status_code == 200
    assert resp.json()["function"] == "CC"


def test_set_function(client, mock_device):
    resp = client.put(
        "/api/v1/function",
        json={"function": "constant_voltage"},
    )
    assert resp.status_code == 200


def test_set_function_invalid(client):
    resp = client.put(
        "/api/v1/function",
        json={"function": "invalid"},
    )
    assert resp.status_code == 422
