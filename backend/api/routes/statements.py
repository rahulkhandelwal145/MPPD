"""Phase 4 — Public Statement Monitor API.

Display-only. Flagged = categories A/B/C, constructive = category D. Category E
(political opinion) is never stored, so it never appears here.

Route ordering is critical: /summary, /run and /pipeline/status must be
declared before /{slug} or FastAPI matches them as slug values.
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import MpStatement, MPProfile
from backend.db.session import get_session
from backend.pipeline import news_pipeline

router = APIRouter(prefix="/statements", tags=["statements"])

CATEGORY_LABELS = {
    "A1": "Sexist / Anti-women",
    "A2": "Casteist / Discriminatory",
    "A3": "Communally Divisive",
    "A4": "Homophobic / Transphobic",
    "A5": "Anti-disabled / Ageist",
    "B1": "Medical Pseudoscience",
    "B2": "Climate / Environment Denial",
    "B3": "Historical Revisionism",
    "B4": "Vaccine / Health Denial",
    "B5": "Economic Reality Denial",
    "C1": "Religious Pseudoscience",
    "C2": "Theocratic Statement",
    "C3": "Religious Incitement",
    "D1": "Data-backed Advocacy",
    "D2": "Specific Policy Demand",
    "D3": "Vulnerable Group Advocacy",
    "D4": "Accountability Demand",
    "D5": "Evidence-based Position",
}

DISCLAIMER = (
    "AI-powered analysis of direct quotes from major English-language Indian "
    "news outlets only. Flags statements that contradict the Indian "
    "Constitution, scientific consensus, or the government's own documented "
    "data. Political opinions are never flagged. Only verbatim quotes are "
    "analysed and may contain classification errors — always read the linked "
    "source article. Regional-language coverage is not included; MPs with less "
    "national visibility may show fewer results regardless of local activity."
)


def _flagged_card(s: MpStatement) -> dict:
    return {
        "id": s.id,
        "category": s.category,
        "category_label": CATEGORY_LABELS.get(s.category, s.category),
        "category_group": s.category_group,
        "verbatim": s.verbatim,
        "context": s.context,
        "constitutional_anchor": s.constitutional_anchor,
        "data_contradicted": s.data_contradicted,
        "reason": s.reason,
        "source": s.source_domain,
        "article_url": s.article_url,
        "published_at": s.published_at,
        "confidence": s.confidence,
    }


def _constructive_card(s: MpStatement) -> dict:
    return {
        "id": s.id,
        "category": s.category,
        "category_label": CATEGORY_LABELS.get(s.category, s.category),
        "category_group": s.category_group,
        "verbatim": s.verbatim,
        "context": s.context,
        "reason": s.reason,
        "source": s.source_domain,
        "article_url": s.article_url,
        "published_at": s.published_at,
        "confidence": s.confidence,
    }


# ─── /summary, /run, /pipeline/status must precede /{slug} ──────────────────────

@router.get("/summary")
async def statements_summary(session: AsyncSession = Depends(get_session)):
    flagged_groups = ("A", "B", "C")

    most_flagged = (await session.execute(
        select(MPProfile.name, MPProfile.prs_slug, func.count(MpStatement.id).label("n"))
        .join(MpStatement, MpStatement.mp_id == MPProfile.id)
        .where(MpStatement.category_group.in_(flagged_groups))
        .group_by(MPProfile.id)
        .order_by(desc("n"))
        .limit(10)
    )).all()

    most_constructive = (await session.execute(
        select(MPProfile.name, MPProfile.prs_slug, func.count(MpStatement.id).label("n"))
        .join(MpStatement, MpStatement.mp_id == MPProfile.id)
        .where(MpStatement.category_group == "D")
        .group_by(MPProfile.id)
        .order_by(desc("n"))
        .limit(10)
    )).all()

    breakdown_rows = (await session.execute(
        select(MpStatement.category, func.count(MpStatement.id))
        .group_by(MpStatement.category)
    )).all()
    category_breakdown = {cat: count for cat, count in breakdown_rows if cat}

    total = await session.scalar(select(func.count(MpStatement.id)))
    total_flagged = await session.scalar(
        select(func.count(MpStatement.id)).where(MpStatement.category_group.in_(flagged_groups))
    )
    total_constructive = await session.scalar(
        select(func.count(MpStatement.id)).where(MpStatement.category_group == "D")
    )

    return {
        "most_flagged_mps": [
            {"name": r.name, "slug": r.prs_slug, "flagged_count": r.n} for r in most_flagged
        ],
        "most_constructive_mps": [
            {"name": r.name, "slug": r.prs_slug, "constructive_count": r.n} for r in most_constructive
        ],
        "category_breakdown": category_breakdown,
        "total_statements_analysed": total or 0,
        "total_flagged": total_flagged or 0,
        "total_constructive": total_constructive or 0,
        "period": "last 30 days",
    }


@router.post("/run")
async def trigger_run(
    background_tasks: BackgroundTasks,
    payload: dict | None = None,
):
    """Trigger the news pipeline as a background task. Optional body:
    {"limit": int, "slug": str} to scope a test run."""
    payload = payload or {}
    limit = payload.get("limit")
    only_slug = payload.get("slug")
    offset = payload.get("offset", 0)
    background_tasks.add_task(news_pipeline.run_all, limit, only_slug, offset)
    return {"started": True}


@router.get("/pipeline/status")
async def pipeline_status(session: AsyncSession = Depends(get_session)):
    return await news_pipeline.last_run_status()


# ─── /{slug} must be last ───────────────────────────────────────────────────────

@router.get("/{slug}")
async def statements_by_slug(
    slug: str,
    days: int = 30,
    group: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    profile = (await session.execute(
        select(MPProfile.id, MPProfile.name).where(MPProfile.prs_slug == slug)
    )).first()
    if profile is None:
        raise HTTPException(status_code=404, detail="MP not found")
    mp_id, mp_name = profile

    cutoff = datetime.utcnow() - timedelta(days=days)
    query = (
        select(MpStatement)
        .where(MpStatement.mp_id == mp_id)
        .where(
            (MpStatement.published_at.is_(None))
            | (MpStatement.published_at >= cutoff)
        )
        .order_by(MpStatement.published_at.desc())
    )
    if group in ("A", "B", "C", "D"):
        query = query.where(MpStatement.category_group == group)

    rows = (await session.execute(query)).scalars().all()

    flagged = [_flagged_card(s) for s in rows if s.category_group in ("A", "B", "C")]
    constructive = [_constructive_card(s) for s in rows if s.category_group == "D"]

    article_ids = {s.article_id for s in rows}

    return {
        "mp_name": mp_name,
        "period": "last 30 days",
        "flagged": flagged,
        "constructive": constructive,
        "articles_analysed": len(article_ids),
        "last_updated": max((s.classified_at for s in rows), default=None),
        "disclaimer": DISCLAIMER,
    }
