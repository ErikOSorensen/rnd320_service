def test_get_device_info(client):
    resp = client.get("/api/v1/device")
    assert resp.status_code == 200
    data = resp.json()
    assert "RND 320-KEL103" in data["model"]
    assert data["status"]["beep"] == "ON"
    assert data["status"]["lock"] == "OFF"
    assert data["device_info"] is not None
