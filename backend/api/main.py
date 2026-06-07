from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.api.routes import mps, pipeline
from backend.api.routes.chat import router as chat_router
from backend.api.routes.integrity import router as integrity_router
from backend.api.routes.statements import router as statements_router
from backend.core.config import settings
from backend.db.models import MpMplads, MpNewsArticle, MpStatement
from backend.db.session import engine
from backend.pipeline.news_pipeline import run_all_sync

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
app.include_router(statements_router, prefix="/api/v1")

scheduler = BackgroundScheduler()


@app.on_event("startup")
async def _ensure_unmanaged_tables():
    """Phase 3's mp_mplads and Phase 4's news tables aren't managed by Alembic —
    create them on startup if missing. checkfirst leaves existing tables (incl.
    Alembic-managed Phase 1 ones) untouched."""
    async with engine.begin() as conn:
        for table in (MpMplads.__table__, MpNewsArticle.__table__, MpStatement.__table__):
            await conn.run_sync(
                lambda sync_conn, t=table: t.create(sync_conn, checkfirst=True)
            )


@app.on_event("startup")
def _start_scheduler():
    """Phase 4 — weekly Public Statement Monitor run, Sunday 02:00."""
    scheduler.add_job(
        run_all_sync,
        trigger="cron",
        day_of_week="sun",
        hour=2,
        minute=0,
        id="weekly_news_pipeline",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Weekly news pipeline scheduled (Sun 02:00)")


@app.on_event("shutdown")
def _stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)


@app.get("/api/v1/health")
def health_check():
    return {"status": "ok", "debug": settings.debug}
