from fastapi import FastAPI
from prometheus_client import Counter, start_http_server
import uvicorn

app = FastAPI()
request_counter = Counter('http_requests_total', 'Total HTTP requests')

@app.get("/")
async def root():
    request_counter.inc()
    return {"message": "Service A is running"}

if __name__ == "__main__":
    start_http_server(8000)
    uvicorn.run(app, host="0.0.0.0", port=8001)