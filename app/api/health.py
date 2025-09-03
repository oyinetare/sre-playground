from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import time

from app.db.database import get_db

router = APIRouter()

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check"""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "checks": {}
    }
    
    # check db
    try:
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"

    return health_status

@router.get("/health/live")
def liveness():
    """Simple liveness check"""
    return {"status": "alive"}

@router.get("/health/ready")
def readiness(db:Session = Depends(get_db)):
    """Readiness check - are we ready for traffic?"""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except:
        return {"status": "not ready"}, 503

@router.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)