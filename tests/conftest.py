from unittest.mock import MagicMock, PropertyMock

import pytest
from fastapi.testclient import TestClient
from kelctl.kelenums import BaudRate, Mode, OnOffState
from kelctl.kellists import BattList

from rnd320_service.device import device_manager
from rnd320_service.main import app


def _make_on_off_button(state: str = "OFF"):
    """Create a mock OnOffButton that tracks on/off state."""
    button = MagicMock()
    current = OnOffState(state)
    button.get.return_value = current
    button.on.side_effect = lambda: button.get.configure_mock(
        return_value=OnOffState("ON")
    )
    button.off.side_effect = lambda: button.get.configure_mock(
        return_value=OnOffState("OFF")
    )
    return button


def _make_toggle(state: str = "OFF"):
    """Create a mock settings toggle."""
    toggle = MagicMock()
    toggle.get.return_value = OnOffState(state)
    return toggle


@pytest.fixture
def mock_device():
    """Create a mock KELSerial device with realistic return values."""
    device = MagicMock()

    # Device info
    type(device).model = PropertyMock(return_value="RND 320-KEL103 V2.60 SN:01234567")
    type(device).device_info = PropertyMock(return_value="DHCP:ON IP:192.168.1.100")
    type(device).is_open = PropertyMock(return_value=True)

    # Status
    status = MagicMock()
    status.beep = OnOffState("ON")
    status.lock = OnOffState("OFF")
    status.baudrate = BaudRate(115200)
    status.trigger = OnOffState("OFF")
    status.comm = OnOffState("ON")
    type(device).status = PropertyMock(return_value=status)

    # Measurements
    type(device).measured_voltage = PropertyMock(return_value=12.05)
    type(device).measured_current = PropertyMock(return_value=1.503)
    type(device).measured_power = PropertyMock(return_value=18.12)

    # Setpoints
    type(device).voltage = PropertyMock(return_value=12.0)
    type(device).current = PropertyMock(return_value=2.0)
    type(device).power = PropertyMock(return_value=24.0)
    type(device).resistance = PropertyMock(return_value=6.0)

    # Function/mode
    type(device).function = PropertyMock(return_value=Mode.constant_current)

    # Input
    device.input = _make_on_off_button("OFF")

    # Settings
    settings = MagicMock()
    type(settings).voltage_limit = PropertyMock(return_value=120.0)
    type(settings).current_limit = PropertyMock(return_value=30.0)
    type(settings).power_limit = PropertyMock(return_value=300.0)
    type(settings).resistance_limit = PropertyMock(return_value=9999.0)
    settings.beep = _make_toggle("ON")
    settings.lock = _make_toggle("OFF")
    settings.dhcp = _make_toggle("ON")
    settings.trigger = _make_toggle("OFF")
    settings.compensation = _make_toggle("OFF")
    type(device).settings = PropertyMock(return_value=settings)

    # Battery
    device.get_batt.return_value = BattList(
        save_slot=1,
        current_range=30.0,
        discharge_current=1.0,
        cutoff_voltage=3.0,
        cutoff_capacity=100.0,
        cutoff_time=600.0,
    )
    device.get_batt_cap.return_value = 1.234
    device.get_batt_time.return_value = 45.2

    return device


@pytest.fixture
def client(mock_device):
    """TestClient with device_manager returning the mock device."""
    device_manager._device = mock_device
    device_manager._lock.acquire(blocking=False)
    device_manager._lock.release()  # ensure lock is free

    original_acquire = device_manager.acquire
    original_release = device_manager.release

    def patched_acquire():
        device_manager._lock.acquire()
        return mock_device

    def patched_release():
        device_manager._lock.release()

    device_manager.acquire = patched_acquire
    device_manager.release = patched_release

    with TestClient(app) as c:
        yield c

    device_manager.acquire = original_acquire
    device_manager.release = original_release
    device_manager._device = None
