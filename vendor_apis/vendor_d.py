from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from collections import deque
import uvicorn
import asyncio

app = FastAPI(title = "Vendor D API")

RATE_LIMIT = 8
WINDOW_SECONDS = 60 
request_times = deque()

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    now = datetime.utcnow()
    cutoff = now - timedelta(seconds=WINDOW_SECONDS)

    while request_times and request_times[0] < cutoff:
        request_times.popleft()

    if len(request_times) >= RATE_LIMIT:
        return JSONResponse(
            status_code = 429,
            content={"error": "Rate limit exceeded", "retry_after": 60}
        )
    request_times.append(now)
    response = await call_next(request)
    return response

@app.get("/product/{product_id}")
async def get_product(product_id: str):
    await asyncio.sleep(0.1)

    return {
        "product_id": product_id,
        "additional_info": {
            "stock":42, 
            "warranty": "1 year",
            "shipping": "Free"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    return {"status":"healthy", "rate_limit": f"{RATE_LIMIT}/{WINDOW_SECONDS}s"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)