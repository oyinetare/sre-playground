from app.middleware.rate_limiter import RateLimiter


# Define rate limits for different operations
class RateLimits:
    # General API limit: 100 requests per minute
    DEFAULT = RateLimiter(rate=100, per=60, burst=110)

    # Strict limit for resource creation: 10 per minute
    CREATE_STUDENT = RateLimiter(rate=10, per=60, burst=15)

    # Auth endpoints: 5 attempts per minute
    AUTH = RateLimiter(rate=5, per=60, burst=5)

    # Search endpoints: 30 per minute
    SEARCH = RateLimiter(rate=30, per=60, burst=40)

    # Admin endpoints: 50 per minute
    ADMIN = RateLimiter(rate=50, per=60, burst=60)

    # Bulk operations: 2 per minute
    BULK = RateLimiter(rate=2, per=60, burst=2)
