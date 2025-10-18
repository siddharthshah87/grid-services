from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys

from app.routers import event
from app.routers import health
from app.routers import stats as api_stats
from app.routers import ven
from app.services import MQTTConsumer, EventCommandService
from app.core.config import settings
from app.dependencies import get_session


# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("uvicorn")

# Global service instances
mqtt_consumer = MQTTConsumer(config=settings, session_factory=get_session)
event_command_service = EventCommandService(config=settings, session_factory=get_session)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting MQTT consumer...")
    await mqtt_consumer.start()
    logger.info("MQTT consumer started")
    
    logger.info("Starting event command service...")
    await event_command_service.start()
    logger.info("Event command service started")
    
    yield
    
    # Shutdown
    logger.info("Stopping event command service...")
    await event_command_service.stop()
    logger.info("Event command service stopped")
    
    logger.info("Stopping MQTT consumer...")
    await mqtt_consumer.stop()
    logger.info("MQTT consumer stopped")


app = FastAPI(
    title="OpenADR VTN Admin API",
    version="0.1.0",
    docs_url=None,
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS (configured for demo environment)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.gridcircuit.link",
        "https://gridcircuit.link",
        "http://localhost:3000",  # For local development
        "http://localhost:5173",  # For Vite dev server
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(api_stats.router, prefix="/api/stats", tags=["Stats"])
app.include_router(ven.router, prefix="/api/vens", tags=["VENs"])
app.include_router(event.router, prefix="/api/events", tags=["Events"])


# Custom docs endpoint
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(openapi_url=app.openapi_url, title=app.title)
