from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys

from app.routers import health, event, ven

app = FastAPI(
    title="OpenADR VTN Admin API",
    version="0.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# CORS (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with frontend origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(ven.router, prefix="/vens", tags=["VENs"])
app.include_router(event.router, prefix="/events", tags=["Events"])

# Startup/shutdown hooks

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("uvicorn")
