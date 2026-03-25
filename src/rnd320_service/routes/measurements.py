from fastapi import APIRouter, HTTPException

from rnd320_service.device import device_manager
from rnd320_service.models import MeasurementsResponse

router = APIRouter(prefix="/api/v1", tags=["measurements"])


@router.get("/measurements", response_model=MeasurementsResponse)
def get_measurements():
    device = device_manager.acquire()
    try:
        return MeasurementsResponse(
            voltage=device.measured_voltage,
            current=device.measured_current,
            power=device.measured_power,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        device_manager.release()
