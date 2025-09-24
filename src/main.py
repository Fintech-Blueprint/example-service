from fastapi import FastAPI

app = FastAPI()

from src.adapters.http.ping_endpoint_controller import router as ping_endpoint_router
from src.adapters.http.health_controller import router as health_router

app.include_router(ping_endpoint_router)
app.include_router(health_router)
