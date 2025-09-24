from fastapi import FastAPI

app = FastAPI()

from src.adapters.http.ping_endpoint_controller import router as ping_endpoint_router
app.include_router(ping_endpoint_router)

from src.adapters.http.broken_ping_service_controller import router as broken_ping_service_router
app.include_router(broken_ping_service_router)
