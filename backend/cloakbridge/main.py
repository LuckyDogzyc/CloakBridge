from __future__ import annotations

from fastapi import FastAPI

from cloakbridge.api.routes import router

app = FastAPI(title="CloakBridge", version="0.1.0")
app.include_router(router)
