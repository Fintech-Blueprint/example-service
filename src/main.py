from fastapi import FastAPI
from prometheus_client import start_http_server
import uvicorn

app = FastAPI()

from src.adapters.http.ping_endpoint_controller import router as ping_endpoint_router
from src.adapters.http.health_controller import router as health_router
from src.adapters.http.metrics_controller import router as metrics_router

app.include_router(ping_endpoint_router)
app.include_router(health_router)
app.include_router(metrics_router)

# Start Prometheus metrics server
start_http_server(9090)
