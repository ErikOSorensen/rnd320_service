import logging
import threading

from kelctl import KELSerial
from kelctl.kelenums import BaudRate

from rnd320_service.config import settings

logger = logging.getLogger(__name__)


class DeviceManager:
    """Thread-safe wrapper around KELSerial."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._device: KELSerial | None = None

    @property
    def connected(self) -> bool:
        return self._device is not None and self._device.is_open

    def connect(self) -> None:
        if self._device is not None:
            return
        logger.info("Connecting to %s at %d baud", settings.port, settings.baudrate)
        self._device = KELSerial(settings.port, BaudRate(settings.baudrate))
        logger.info("Connected")

    def disconnect(self) -> None:
        if self._device is None:
            return
        logger.info("Disconnecting from device")
        try:
            self._device.close()
        except Exception:
            logger.exception("Error closing device")
        self._device = None

    def acquire(self) -> KELSerial:
        """Acquire the lock and return the device. Caller MUST call release()."""
        self._lock.acquire()
        if self._device is None or not self._device.is_open:
            self._lock.release()
            raise RuntimeError("Device not connected")
        return self._device

    def release(self) -> None:
        self._lock.release()


device_manager = DeviceManager()
