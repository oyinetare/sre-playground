from prometheus_client import Counter, Histogram

# basic metrics
http_requests_total = Counter(
    "http_requests_total",
    'Total HTTP requests',
    ["method", "endpoint", "status"]
)

http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration'
)

students_created_total = Counter(
    'students_created_total',
    'Total students created'
)