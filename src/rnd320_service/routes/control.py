from fastapi import APIRouter, HTTPException

from kelctl.kelenums import Mode

from rnd320_service.device import device_manager
from rnd320_service.models import (
    FunctionRequest,
    FunctionResponse,
    InputStateRequest,
    InputStateResponse,
    SetpointMode,
    SetpointRequest,
    SetpointResponse,
)

router = APIRouter(prefix="/api/v1", tags=["control"])

_MODE_MAP = {
    SetpointMode.constant_voltage: Mode.constant_voltage,
    SetpointMode.constant_current: Mode.constant_current,
    SetpointMode.constant_resistance: Mode.constant_resistance,
    SetpointMode.constant_power: Mode.constant_power,
    SetpointMode.short: Mode.short,
}


# --- Input ---


@router.get("/input", response_model=InputStateResponse)
def get_input():
    device = device_manager.acquire()
    try:
        state = device.input.get()
        return InputStateResponse(state=state.b)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        device_manager.release()


@router.put("/input", response_model=InputStateResponse)
def set_input(request: InputStateRequest):
    state = request.state.upper()
    if state not in ("ON", "OFF"):
        raise HTTPException(status_code=400, detail="state must be 'ON' or 'OFF'")

    device = device_manager.acquire()
    try:
        if state == "ON":
            device.input.on()
        else:
            device.input.off()
        current = device.input.get()
        return InputStateResponse(state=current.b)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        device_manager.release()


# --- Setpoint ---


@router.get("/setpoint", response_model=SetpointResponse)
def get_setpoint():
    device = device_manager.acquire()
    try:
        func = device.function
        return SetpointResponse(
            mode=func.value if func else None,
            voltage=device.voltage,
            current=device.current,
            power=device.power,
            resistance=device.resistance,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        device_manager.release()


@router.put("/setpoint", response_model=SetpointResponse)
def set_setpoint(request: SetpointRequest):
    device = device_manager.acquire()
    try:
        if request.mode == SetpointMode.constant_voltage:
            device.voltage = request.value
        elif request.mode == SetpointMode.constant_current:
            device.current = request.value
        elif request.mode == SetpointMode.constant_resistance:
            device.resistance = request.value
        elif request.mode == SetpointMode.constant_power:
            device.power = request.value
        elif request.mode == SetpointMode.short:
            device.function = Mode.short

        func = device.function
        return SetpointResponse(
            mode=func.value if func else None,
            voltage=device.voltage,
            current=device.current,
            power=device.power,
            resistance=device.resistance,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        device_manager.release()


# --- Function ---


@router.get("/function", response_model=FunctionResponse)
def get_function():
    device = device_manager.acquire()
    try:
        func = device.function
        return FunctionResponse(function=func.value if func else None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        device_manager.release()


@router.put("/function", response_model=FunctionResponse)
def set_function(request: FunctionRequest):
    device = device_manager.acquire()
    try:
        device.function = _MODE_MAP[request.function]
        func = device.function
        return FunctionResponse(function=func.value if func else None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        device_manager.release()
