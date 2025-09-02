from fastapi import FastAPI, Response
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
import time

app = FastAPI(title="SRE Playground API", version="1.0.0")

# Simple basic metric
request_count = Counter('request_total', 'Total requests')

@app.get("/")
def root():
    request_count.inc()
    return {"message": "SRE Playground API", "status": "running"}

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": time.time()
    }
    
@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)