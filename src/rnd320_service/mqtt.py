import json
import logging
import threading
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
        self._connected = False

    @property
    def enabled(self) -> bool:
        return settings.mqtt_broker is not None

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            logger.info("MQTT connected to %s:%d", settings.mqtt_broker, settings.mqtt_port)
            self._connected = True
        else:
            logger.warning("MQTT connection returned code %s", rc)
            self._connected = False

    def _on_disconnect(self, client, userdata, flags, rc, properties=None):
        self._connected = False
        if rc == 0:
            logger.info("MQTT disconnected cleanly")
        else:
            logger.warning("MQTT connection lost (rc=%s), will reconnect automatically", rc)

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
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.reconnect_delay_set(min_delay=1, max_delay=60)

        if settings.mqtt_username:
            self._client.username_pw_set(settings.mqtt_username, settings.mqtt_password)

        try:
            self._client.connect(settings.mqtt_broker, settings.mqtt_port)
        except Exception:
            logger.exception("Failed initial MQTT connection to %s:%d",
                             settings.mqtt_broker, settings.mqtt_port)
            self._client = None
            return

        # loop_start() runs a background thread that handles reconnection
        self._client.loop_start()
        logger.info("MQTT publisher started, publishing to '%s' every %.1fs",
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
        self._connected = False
        logger.info("MQTT publisher stopped")

    def _publish_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._publish_once()
            except Exception:
                logger.exception("MQTT publish error")
            self._stop_event.wait(timeout=settings.mqtt_interval)

    def _publish_once(self) -> None:
        if self._client is None or not self._connected:
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
