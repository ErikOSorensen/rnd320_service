import os


class Settings:
    port: str = os.environ.get("RND320_PORT", "/dev/ttyACM0")
    baudrate: int = int(os.environ.get("RND320_BAUDRATE", "115200"))
    host: str = os.environ.get("RND320_HOST", "0.0.0.0")
    http_port: int = int(os.environ.get("RND320_HTTP_PORT", "8320"))

    # MQTT (optional — publishing is disabled when broker is not set)
    mqtt_broker: str | None = os.environ.get("RND320_MQTT_BROKER")
    mqtt_port: int = int(os.environ.get("RND320_MQTT_PORT", "1883"))
    mqtt_topic: str = os.environ.get("RND320_MQTT_TOPIC", "rnd320/measurements")
    mqtt_interval: float = float(os.environ.get("RND320_MQTT_INTERVAL", "1.0"))
    mqtt_username: str | None = os.environ.get("RND320_MQTT_USERNAME")
    mqtt_password: str | None = os.environ.get("RND320_MQTT_PASSWORD")


settings = Settings()
