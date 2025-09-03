from fastapi import FastAPI
import logging
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.db.database import engine
from app.models.student import Base, Student
from app.api import health, students

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
