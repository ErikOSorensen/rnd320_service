import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from rnd320_service.config import settings
from rnd320_service.device import device_manager
from rnd320_service.mqtt import mqtt_publisher
from rnd320_service.routes import battery, control, device, measurements, settings as settings_routes

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        device_manager.connect()
    except Exception:
        logger.exception("Failed to connect to device on startup")
    mqtt_publisher.start()
    yield
    mqtt_publisher.stop()
    device_manager.disconnect()


app = FastAPI(
    title="RND320 Service",
    description="REST API for RND320 / Korad KEL103 electronic DC load",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(device.router)
app.include_router(measurements.router)
app.include_router(control.router)
app.include_router(settings_routes.router)
app.include_router(battery.router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "device_connected": device_manager.connected}


def main():
    uvicorn.run(
        "rnd320_service.main:app",
        host=settings.host,
        port=settings.http_port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
