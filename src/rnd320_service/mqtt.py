import json
import logging
import threading
import time
from datetime import datetime, timezone

from rnd320_service.config import settings
from rnd320_service.device import device_manager

logger = logging.getLogger(__name__)


class MQTTPublisher:
    """Periodically publishes measurements to an MQTT broker."""

    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._client = None

    @property
    def enabled(self) -> bool:
        return settings.mqtt_broker is not None

    def start(self) -> None:
        if not self.enabled:
            return

        try:
            import paho.mqtt.client as mqtt
        except ImportError:
            logger.error(
                "MQTT broker configured but paho-mqtt is not installed. "
                "Install with: uv sync --extra mqtt"
            )
            return

        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        if settings.mqtt_username:
            self._client.username_pw_set(settings.mqtt_username, settings.mqtt_password)

        try:
            self._client.connect(settings.mqtt_broker, settings.mqtt_port)
        except Exception:
            logger.exception("Failed to connect to MQTT broker %s:%d",
                             settings.mqtt_broker, settings.mqtt_port)
            self._client = None
            return

        self._client.loop_start()
        logger.info("MQTT connected to %s:%d, publishing to '%s' every %.1fs",
                     settings.mqtt_broker, settings.mqtt_port,
                     settings.mqtt_topic, settings.mqtt_interval)

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._publish_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._thread is None:
            return
        self._stop_event.set()
        self._thread.join(timeout=5)
        self._thread = None
        if self._client is not None:
            self._client.loop_stop()
            self._client.disconnect()
            self._client = None
        logger.info("MQTT publisher stopped")

    def _publish_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._publish_once()
            except Exception:
                logger.exception("MQTT publish error")
            self._stop_event.wait(timeout=settings.mqtt_interval)

    def _publish_once(self) -> None:
        if self._client is None:
            return

        device = device_manager.acquire()
        try:
            input_state = device.input.get().b
            if input_state != "ON":
                return

            payload = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "voltage": device.measured_voltage,
                "current": device.measured_current,
                "power": device.measured_power,
            }
        finally:
            device_manager.release()

        self._client.publish(settings.mqtt_topic, json.dumps(payload))


mqtt_publisher = MQTTPublisher()
