from enum import Enum

from pydantic import BaseModel


class SetpointMode(str, Enum):
    constant_voltage = "constant_voltage"
    constant_current = "constant_current"
    constant_resistance = "constant_resistance"
    constant_power = "constant_power"
    short = "short"


class DeviceStatus(BaseModel):
    beep: str | None = None
    lock: str | None = None
    baudrate: int | None = None
    trigger: str | None = None
    comm: str | None = None


class DeviceInfoResponse(BaseModel):
    model: str | None = None
    status: DeviceStatus | None = None
    device_info: str | None = None


class MeasurementsResponse(BaseModel):
    voltage: float | None = None
    current: float | None = None
    power: float | None = None


class InputStateResponse(BaseModel):
    state: str  # "ON" or "OFF"


class InputStateRequest(BaseModel):
    state: str  # "ON" or "OFF"


class SetpointResponse(BaseModel):
    mode: str | None = None
    voltage: float | None = None
    current: float | None = None
    power: float | None = None
    resistance: float | None = None


class SetpointRequest(BaseModel):
    mode: SetpointMode
    value: float


class FunctionResponse(BaseModel):
    function: str | None = None


class FunctionRequest(BaseModel):
    function: SetpointMode


class SettingsResponse(BaseModel):
    voltage_limit: float | None = None
    current_limit: float | None = None
    power_limit: float | None = None
    resistance_limit: float | None = None
    beep: str | None = None
    lock: str | None = None
    dhcp: str | None = None
    trigger: str | None = None
    compensation: str | None = None


class SettingsUpdate(BaseModel):
    voltage_limit: float | None = None
    current_limit: float | None = None
    power_limit: float | None = None
    resistance_limit: float | None = None
    beep: str | None = None
    lock: str | None = None
    dhcp: str | None = None
    trigger: str | None = None
    compensation: str | None = None


class ErrorResponse(BaseModel):
    detail: str
