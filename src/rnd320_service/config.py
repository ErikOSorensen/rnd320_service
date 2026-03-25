import os


class Settings:
    port: str = os.environ.get("RND320_PORT", "/dev/ttyACM0")
    baudrate: int = int(os.environ.get("RND320_BAUDRATE", "115200"))
    host: str = os.environ.get("RND320_HOST", "0.0.0.0")
    http_port: int = int(os.environ.get("RND320_HTTP_PORT", "8320"))


settings = Settings()
