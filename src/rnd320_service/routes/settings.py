from fastapi import APIRouter, HTTPException

from rnd320_service.device import device_manager
from rnd320_service.models import SettingsResponse, SettingsUpdate

router = APIRouter(prefix="/api/v1", tags=["settings"])


def _get_toggle(toggle) -> str | None:
    try:
        return toggle.get().b
    except Exception:
        return None


@router.get("/settings", response_model=SettingsResponse)
def get_settings():
    device = device_manager.acquire()
    try:
        s = device.settings
        return SettingsResponse(
            voltage_limit=s.voltage_limit,
            current_limit=s.current_limit,
            power_limit=s.power_limit,
            resistance_limit=s.resistance_limit,
            beep=_get_toggle(s.beep),
            lock=_get_toggle(s.lock),
            dhcp=_get_toggle(s.dhcp),
            trigger=_get_toggle(s.trigger),
            compensation=_get_toggle(s.compensation),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        device_manager.release()


@router.patch("/settings", response_model=SettingsResponse)
def update_settings(update: SettingsUpdate):
    device = device_manager.acquire()
    try:
        s = device.settings

        if update.voltage_limit is not None:
            s.voltage_limit = update.voltage_limit
        if update.current_limit is not None:
            s.current_limit = update.current_limit
        if update.power_limit is not None:
            s.power_limit = update.power_limit
        if update.resistance_limit is not None:
            s.resistance_limit = update.resistance_limit

        if update.beep is not None:
            (s.beep.on if update.beep.upper() == "ON" else s.beep.off)()
        if update.lock is not None:
            (s.lock.on if update.lock.upper() == "ON" else s.lock.off)()
        if update.dhcp is not None:
            (s.dhcp.on if update.dhcp.upper() == "ON" else s.dhcp.off)()
        if update.trigger is not None:
            (s.trigger.on if update.trigger.upper() == "ON" else s.trigger.off)()
        if update.compensation is not None:
            (s.compensation.on if update.compensation.upper() == "ON" else s.compensation.off)()

        return SettingsResponse(
            voltage_limit=s.voltage_limit,
            current_limit=s.current_limit,
            power_limit=s.power_limit,
            resistance_limit=s.resistance_limit,
            beep=_get_toggle(s.beep),
            lock=_get_toggle(s.lock),
            dhcp=_get_toggle(s.dhcp),
            trigger=_get_toggle(s.trigger),
            compensation=_get_toggle(s.compensation),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        device_manager.release()
