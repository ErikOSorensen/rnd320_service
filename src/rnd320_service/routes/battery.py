from fastapi import APIRouter, HTTPException

from kelctl.kellists import BattList

from rnd320_service.device import device_manager
from rnd320_service.models import (
    BatteryConfigRequest,
    BatteryConfigResponse,
    BatteryStatusResponse,
)

router = APIRouter(prefix="/api/v1/battery", tags=["battery"])


@router.get("/config/{slot}", response_model=BatteryConfigResponse)
def get_battery_config(slot: int):
    if not 1 <= slot <= 10:
        raise HTTPException(status_code=400, detail="slot must be 1-10")

    device = device_manager.acquire()
    try:
        batt = device.get_batt(slot)
        return BatteryConfigResponse(
            save_slot=batt.save_slot,
            current_range=batt.current_range,
            discharge_current=batt.discharge_current,
            cutoff_voltage=batt.cutoff_voltage,
            cutoff_capacity=batt.cutoff_capacity,
            cutoff_time=batt.cutoff_time,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        device_manager.release()


@router.put("/config", response_model=BatteryConfigResponse)
def set_battery_config(request: BatteryConfigRequest):
    if not 1 <= request.save_slot <= 10:
        raise HTTPException(status_code=400, detail="save_slot must be 1-10")

    device = device_manager.acquire()
    try:
        batt = BattList(
            save_slot=request.save_slot,
            current_range=request.current_range,
            discharge_current=request.discharge_current,
            cutoff_voltage=request.cutoff_voltage,
            cutoff_capacity=request.cutoff_capacity,
            cutoff_time=request.cutoff_time,
        )
        device.set_batt(batt, recall=True)
        return BatteryConfigResponse(
            save_slot=request.save_slot,
            current_range=request.current_range,
            discharge_current=request.discharge_current,
            cutoff_voltage=request.cutoff_voltage,
            cutoff_capacity=request.cutoff_capacity,
            cutoff_time=request.cutoff_time,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        device_manager.release()


@router.post("/recall/{slot}", response_model=BatteryConfigResponse)
def recall_battery_config(slot: int):
    if not 1 <= slot <= 10:
        raise HTTPException(status_code=400, detail="slot must be 1-10")

    device = device_manager.acquire()
    try:
        device.recall_batt(slot)
        batt = device.get_batt(slot)
        return BatteryConfigResponse(
            save_slot=batt.save_slot,
            current_range=batt.current_range,
            discharge_current=batt.discharge_current,
            cutoff_voltage=batt.cutoff_voltage,
            cutoff_capacity=batt.cutoff_capacity,
            cutoff_time=batt.cutoff_time,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        device_manager.release()


@router.get("/status", response_model=BatteryStatusResponse)
def get_battery_status():
    device = device_manager.acquire()
    try:
        input_state = device.input.get().b
        func = device.function
        func_str = func.value if func else None
        running = input_state == "ON" and func_str == "BATTERY"

        return BatteryStatusResponse(
            capacity=device.get_batt_cap(),
            time=device.get_batt_time(),
            input=input_state,
            function=func_str,
            running=running,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        device_manager.release()
