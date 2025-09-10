import hashlib
import json
import time

import redis
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitExceeded(HTTPException):
    def __init__(self, retry_after: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )


class RateLimiter:
    """Token bucket rate limiter with Redis backend"""

    def __init__(
        self,
        rate: int = 10,  # requests
        per: int = 60,  # seconds
        burst: int | None = None,
    ):
        self.rate = rate
        self.per = per
        self.burst = burst or rate  # Allow burst equal to rate by default
        self.redis_client: redis.Redis | None = None

    def initialise(self):
        """initialise Redis connection"""
        try:
            self.redis_client = redis.Redis(
                host="redis", port=6379, decode_responses=True
            )
            self.redis_client.ping()
            print("Rate limiter initialised with Redis")
        except Exception as e:
            print(f"Rate limiter Redis init failed: {e}")
            # Fall back to in-memory if Redis is down
            self.redis_client = None
            self._memory_store = {}

    def _get_key(self, identifier: str, endpoint: str) -> str:
        """Generate Redis key for rate limit bucket"""
        return f"rate_limit:{endpoint}:{identifier}"

    def _get_bucket(self, key: str) -> dict:
        """Get current token bucket state"""
        if self.redis_client:
            try:
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                print(f"Redis error: {e}")
        else:
            # In-memory fallback
            if hasattr(self, "_memory_store") and key in self._memory_store:
                return self._memory_store[key]

        # Initiase new bucket - ALWAYS return a dict
        return {"tokens": self.burst, "last_refill": time.time()}

    def _save_bucket(self, key: str, bucket: dict):
        """Save bucket state"""
        if self.redis_client:
            self.redis_client.setex(
                key,
                self.per * 2,  # Expire after 2x the rate limit window
                json.dumps(bucket),
            )
        else:
            self._memory_store[key] = bucket

    def check_rate_limit(self, identifier: str, endpoint: str) -> tuple[bool, int]:
        """
        Check if request is within rate limit
        Returns: (allowed: bool, retry_after: int)
        """
        print(f"Rate limit check for {identifier} on {endpoint}")  # Debug

        key = self._get_key(identifier, endpoint)
        bucket = self._get_bucket(key)

        now = time.time()
        time_passed = now - bucket["last_refill"]

        # Refill tokens based on time passed
        tokens_to_add = (time_passed / self.per) * self.rate
        bucket["tokens"] = min(self.burst, bucket["tokens"] + tokens_to_add)
        bucket["last_refill"] = now

        if bucket["tokens"] >= 1:
            # Allow request
            bucket["tokens"] -= 1
            self._save_bucket(key, bucket)
            return True, 0
        else:
            # Calculate retry after
            tokens_needed = 1 - bucket["tokens"]
            seconds_until_token = (tokens_needed / self.rate) * self.per
            retry_after = int(seconds_until_token) + 1

            self._save_bucket(key, bucket)
            return False, retry_after


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with different limits per endpoint"""

    def __init__(self, app, default_limit: RateLimiter):
        super().__init__(app)
        self.default_limit = default_limit
        self.endpoint_limits = {}

        # initialise rate limiter
        self.default_limit.initialise()

    def add_endpoint_limit(self, path: str, limiter: RateLimiter):
        """Add specific rate limit for an endpoint"""
        limiter.initialise()
        self.endpoint_limits[path] = limiter

    def _get_identifier(self, request: Request) -> str:
        """Get identifier for rate limiting (IP + User if authenticated)"""
        # Get IP address
        ip = request.client.host

        # If authenticated, include user ID
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            # Hash token to use as identifier (don't decode JWT here)
            token_hash = hashlib.md5(auth_header.encode()).hexdigest()[:8]
            return f"{ip}:{token_hash}"

        return ip

    def _get_limiter_for_path(self, path: str) -> RateLimiter:
        """Get appropriate rate limiter for path"""
        # Check exact match first
        if path in self.endpoint_limits:
            return self.endpoint_limits[path]

        # Check prefix match
        for endpoint, limiter in self.endpoint_limits.items():
            if path.startswith(endpoint):
                return limiter

        return self.default_limit

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and metrics
        print(f"Rate limiter called for: {request.url.path}")  # Add this

        if request.url.path in ["/health", "/health/live", "/health/ready", "/metrics"]:
            return await call_next(request)

        identifier = self._get_identifier(request)
        limiter = self._get_limiter_for_path(request.url.path)

        allowed, retry_after = limiter.check_rate_limit(identifier, request.url.path)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded", "retry_after": retry_after},
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limiter.rate),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + retry_after),
                },
            )

        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limiter.rate)
        # Note: Getting exact remaining would require another Redis call

        return response
