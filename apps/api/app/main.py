from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger

from app.routers import aqi, forecast, alerts, health
from app.db.database import check_db_connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("BreatheSafe NG API starting...")
    check_db_connection()
    yield
    logger.info("BreatheSafe NG API shutting down...")


app = FastAPI(
    title="BreatheSafe NG API",
    description="Real-time AQI forecasting for Nigerian cities",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://breathesafe.ng"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router,   prefix="/health",   tags=["Health"])
app.include_router(aqi.router,      prefix="/aqi",      tags=["AQI"])
app.include_router(forecast.router, prefix="/forecast", tags=["Forecast"])
app.include_router(alerts.router,   prefix="/alerts",   tags=["Alerts"])


@app.get("/")
def root():
    return {"message": "BreatheSafe NG API", "status": "running", "version": "1.0.0"}