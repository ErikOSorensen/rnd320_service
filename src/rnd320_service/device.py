import logging
import threading

from kelctl import KELSerial
from kelctl.kelenums import BaudRate

from rnd320_service.config import settings

logger = logging.getLogger(__name__)


class DeviceManager:
    """Thread-safe wrapper around KELSerial with automatic reconnection."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._device: KELSerial | None = None

    @property
    def connected(self) -> bool:
        return self._device is not None and self._device.is_open

    def connect(self) -> None:
        """Open a new serial connection to the device."""
        self._close_existing()
        logger.info("Connecting to %s at %d baud", settings.port, settings.baudrate)
        self._device = KELSerial(settings.port, BaudRate(settings.baudrate))
        logger.info("Connected")

    def disconnect(self) -> None:
        """Close the serial connection."""
        if self._device is None:
            return
        logger.info("Disconnecting from device")
        self._close_existing()

    def _close_existing(self) -> None:
        if self._device is None:
            return
        try:
            self._device.close()
        except Exception:
            logger.exception("Error closing device")
        self._device = None

    def _probe(self) -> bool:
        """Send a harmless query to check if the device is responsive."""
        if self._device is None:
            return False
        try:
            self._device.model
            return True
        except Exception:
            return False

    def acquire(self) -> KELSerial:
        """Acquire the lock and return a working device handle.

        If the device is not connected or not responsive, attempts to
        reconnect once. Raises RuntimeError if reconnection fails.
        Caller MUST call release() when done.
        """
        self._lock.acquire()
        try:
            if self._probe():
                return self._device  # type: ignore[return-value]

            # Connection is dead or was never established — try to reconnect
            logger.warning("Device not responsive, attempting reconnection")
            try:
                self.connect()
            except Exception:
                logger.exception("Reconnection failed")
                raise RuntimeError(
                    f"Device not connected and reconnection to {settings.port} failed"
                )
            return self._device  # type: ignore[return-value]
        except BaseException:
            self._lock.release()
            raise

    def release(self) -> None:
        self._lock.release()


device_manager = DeviceManager()
