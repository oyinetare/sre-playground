from fastapi import FastAPI
import logging
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.db.database import engine
from app.models.student import Base, Student
from app.api import health, students
from app.core.metrics import http_request_duration, http_requests_total
from app.services.sqs_service import sqs_service

import time

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    logger.info(f"Starting {settings.app_name} in {settings.environment} mode")
    
    # create db tables
    Base.metadata.create_all(bind=engine)
    
    # initialise SQS
    sqs_service.initialise()
    
    logger.info("Database tables created")
    
    yield
    
    # shutdown
    logger.info("Shutting down")

app = FastAPI(title=settings.app_name, lifespan=lifespan)

# api handlers
app.include_router(health.router, tags=["health"])
app.include_router(students.router, prefix="/api/v1", tags=["students"])

@app.get("/")
def root():
    return {"app": settings.app_name,"environment": settings.environment , "status": "running"}

@app.middleware("http")
async def add_metrics(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    http_request_duration.observe(duration)
    
    return response