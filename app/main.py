import asyncio
import logging
import signal
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import health, students
from app.core.config import get_settings
from app.core.metrics import http_request_duration, http_requests_total
from app.core.rate_limits import RateLimits
from app.db.database import engine
from app.middleware.rate_limiter import RateLimitMiddleware
from app.models.student import Base
from app.services.audit_service import audit_service
from app.services.cache_service import cache_service
from app.services.slo_service import slo_service
from app.services.sqs_service import sqs_service

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

# global flag for shutdown
shutdown_event = asyncio.Event()


def signal_handler(sig, frame):
    logger.info("Received shutdown signal")
    shutdown_event.set()


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


async def periodic_slo_calculation():
    """Calculate SLOs every minute"""
    while True:
        try:
            await slo_service.calculate_slis()
            logger.info("SLO metrics updated")
        except Exception as e:
            logger.error(f"Failed to calculate SLOs: {e}")

        await asyncio.sleep(60)  # Every minute


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    logger.info(f"Starting {settings.app_name} in {settings.environment} mode")

    # create db tables
    Base.metadata.create_all(bind=engine)

    # initialise services
    sqs_service.initialise()
    audit_service.initialise()
    cache_service.initialise()

    logger.info("Database tables created")

    slo_task = asyncio.create_task(periodic_slo_calculation())

    yield

    # shutdown
    slo_task.cancel()
    logger.info("Shutting down gracefully")


app = FastAPI(title=settings.app_name, lifespan=lifespan)

# Create rate limiter configuration
rate_limiter_config = {
    "/api/v1/students": RateLimits.CREATE_STUDENT,
    "/auth/token": RateLimits.AUTH,
    # "/api/v1/students/search": RateLimits.SEARCH,
    # "/api/v1/admin": RateLimits.ADMIN,
    # "/api/v1/students/bulk": RateLimits.BULK,
}


# Add rate limiting middleware with configuration
class ConfiguredRateLimitMiddleware(RateLimitMiddleware):
    def __init__(self, app, default_limit):
        super().__init__(app, default_limit)
        # Add endpoint limits during initialization
        for path, limiter in rate_limiter_config.items():
            self.add_endpoint_limit(path, limiter)


app.add_middleware(ConfiguredRateLimitMiddleware, default_limit=RateLimits.DEFAULT)

# Simple rate limiting for testing
# request_counts = {}

# @app.middleware("http")
# async def simple_rate_limit(request: Request, call_next):
#     if request.url.path == "/api/v1/students" and request.method == "POST":
#         client_ip = request.client.host
#         current_count = request_counts.get(client_ip, 0)

#         if current_count >= 10:
#             return JSONResponse(
#                 status_code=429,
#                 content={"error": "Rate limit exceeded"},
#                 headers={"Retry-After": "60"}
#             )

#         request_counts[client_ip] = current_count + 1

#     return await call_next(request)

# api handlers
app.include_router(health.router, tags=["health"])
app.include_router(students.router, prefix="/api/v1", tags=["students"])


@app.get("/")
def root():
    return {
        "app": settings.app_name,
        "environment": settings.environment,
        "status": "running",
    }


@app.middleware("http")
async def add_metrics(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    http_requests_total.labels(
        method=request.method, endpoint=request.url.path, status=response.status_code
    ).inc()

    http_request_duration.observe(duration)

    return response
