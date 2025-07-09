from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import ven, event, health
from app.db import database

app = FastAPI(
    title="OpenADR VTN Admin API",
    version="0.1.0"
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
app.include_router(ven.router, prefix="/vens", tags=["VENs"])
app.include_router(event.router, prefix="/events", tags=["Events"])
app.include_router(health.router, prefix="/health", tags=["Health"])

# Startup/shutdown hooks
@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
