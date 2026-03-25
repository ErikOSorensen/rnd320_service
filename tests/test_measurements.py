def test_get_measurements(client):
    resp = client.get("/api/v1/measurements")
    assert resp.status_code == 200
    data = resp.json()
    assert data["voltage"] == 12.05
    assert data["current"] == 1.503
    assert data["power"] == 18.12
