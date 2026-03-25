import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from kelctl.kelerrors import InvalidModeError, NoModeSetError, ValueOutOfLimitError

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


@app.exception_handler(ValueOutOfLimitError)
async def value_out_of_limit_handler(request: Request, exc: ValueOutOfLimitError):
    return JSONResponse(
        status_code=400,
        content={
            "detail": f"Value {exc.value} exceeds device limit of {exc.limit}",
        },
    )


@app.exception_handler(NoModeSetError)
async def no_mode_set_handler(request: Request, exc: NoModeSetError):
    return JSONResponse(
        status_code=400,
        content={"detail": f"Mode '{exc.mode}' cannot be set directly"},
    )


@app.exception_handler(InvalidModeError)
async def invalid_mode_handler(request: Request, exc: InvalidModeError):
    return JSONResponse(
        status_code=400,
        content={"detail": f"Invalid device mode: {exc.mode}"},
    )


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    if "not connected" in str(exc).lower():
        return JSONResponse(
            status_code=503,
            content={"detail": str(exc)},
        )
    raise exc


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
