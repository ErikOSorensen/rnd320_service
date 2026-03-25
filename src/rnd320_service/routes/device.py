from fastapi import APIRouter, HTTPException

from rnd320_service.device import device_manager
from rnd320_service.models import DeviceInfoResponse, DeviceStatus

router = APIRouter(prefix="/api/v1", tags=["device"])


@router.get("/device", response_model=DeviceInfoResponse)
def get_device_info():
    device = device_manager.acquire()
    try:
        model = device.model
        status = device.status
        device_info = device.device_info

        status_out = None
        if status is not None:
            status_out = DeviceStatus(
                beep=status.beep.b if status.beep else None,
                lock=status.lock.b if status.lock else None,
                baudrate=status.baudrate.b if status.baudrate else None,
                trigger=status.trigger.b if status.trigger else None,
                comm=status.comm.b if status.comm else None,
            )

        return DeviceInfoResponse(
            model=model,
            status=status_out,
            device_info=device_info,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        device_manager.release()
