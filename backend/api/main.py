from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import mps, pipeline
from backend.api.routes.chat import router as chat_router
from backend.api.routes.integrity import router as integrity_router
from backend.core.config import settings

app = FastAPI(
    title="MP Scorer API",
    version="0.1.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mps.router, prefix="/api/v1")
app.include_router(pipeline.router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(integrity_router, prefix="/api/v1")


@app.get("/api/v1/health")
def health_check():
    return {"status": "ok", "debug": settings.debug}
