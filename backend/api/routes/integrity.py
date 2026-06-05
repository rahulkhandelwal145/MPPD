from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.agents import myneta_pipeline
from backend.core.assets import asset_growth, asset_growth_first, asset_series
from backend.db.models import MpAffidavit, MpAssetHistory, MpCriminalCase, MPProfile, PipelineRun
from backend.db.session import get_session

router = APIRouter(prefix="/integrity", tags=["integrity"])

DISCLAIMER = (
    "Source: Association for Democratic Reforms (ADR) / myneta.info. "
    "Data from self-sworn affidavits filed with the Election Commission of India "
    "during the 2024 Lok Sabha election. Criminal cases are pending allegations, "
    "not convictions. ADR does not modify ECI records."
)


# ─── /summary must be declared before /{slug} ──────────────────────────────────

@router.get("/summary")
async def integrity_summary(session: AsyncSession = Depends(get_session)):
    total_with_cases = await session.scalar(
        select(func.count()).where(MpAffidavit.total_criminal_cases > 0)
    )
    total_with_serious = await session.scalar(
        select(func.count()).where(MpAffidavit.has_serious_cases.is_(True))
    )
    total_convicted = await session.scalar(
        select(func.count()).where(MpAffidavit.has_conviction.is_(True))
    )
    total_crorepati = await session.scalar(
        select(func.count()).where(MpAffidavit.total_assets >= 10_000_000)
    )
    avg_assets = await session.scalar(
        select(func.avg(MpAffidavit.total_assets)).where(MpAffidavit.total_assets.isnot(None))
    )

    most_row = (await session.execute(
        select(MpAffidavit.candidate_name, MpAffidavit.total_assets)
        .where(MpAffidavit.total_assets.isnot(None))
        .order_by(MpAffidavit.total_assets.desc())
        .limit(1)
    )).first()

    least_row = (await session.execute(
        select(MpAffidavit.candidate_name, MpAffidavit.total_assets)
        .where(MpAffidavit.total_assets.isnot(None))
        .order_by(MpAffidavit.total_assets.asc())
        .limit(1)
    )).first()

    return {
        "total_with_cases": total_with_cases or 0,
        "total_with_serious_cases": total_with_serious or 0,
        "total_convicted": total_convicted or 0,
        "total_crorepati": total_crorepati or 0,
        "avg_assets": float(avg_assets) if avg_assets else None,
        "most_assets": {
            "name": most_row.candidate_name,
            "amount": most_row.total_assets,
        } if most_row else None,
        "least_assets": {
            "name": least_row.candidate_name,
            "amount": least_row.total_assets,
        } if least_row else None,
        "disclaimer": DISCLAIMER,
    }


@router.get("/unmatched")
async def integrity_unmatched(session: AsyncSession = Depends(get_session)):
    rows = (await session.execute(
        select(
            MpAffidavit.candidate_name,
            MpAffidavit.myneta_candidate_id,
            MpAffidavit.best_match_name,
            MpAffidavit.best_match_score,
        ).where(MpAffidavit.match_confidence.in_(["low", "none"]))
        .order_by(MpAffidavit.candidate_name)
    )).all()

    return {
        "unmatched": [
            {
                "candidate_name": r.candidate_name,
                "myneta_id": r.myneta_candidate_id,
                "best_match": r.best_match_name,
                "score": r.best_match_score,
            }
            for r in rows
        ]
    }


@router.post("/scrape")
async def trigger_scrape(
    payload: dict,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    force_refresh = bool(payload.get("force_refresh", False))
    run = PipelineRun(status="running", mps_scraped=0, errors=[])
    session.add(run)
    await session.commit()
    await session.refresh(run)

    background_tasks.add_task(myneta_pipeline.run, force_refresh)
    return {"run_id": run.id}


@router.get("/scrape/status/{run_id}")
async def scrape_status(run_id: int, session: AsyncSession = Depends(get_session)):
    run = await session.get(PipelineRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    return {
        "run_id": run.id,
        "status": run.status,
        "scraped": run.mps_scraped,
        "failed": run.errors or [],
        "started_at": run.started_at,
        "completed_at": run.completed_at,
    }


# ─── /{slug} must be last ───────────────────────────────────────────────────────

@router.get("/{slug}")
async def integrity_by_slug(slug: str, session: AsyncSession = Depends(get_session)):
    # Join mp_affidavits via mp_profiles.prs_slug
    profile_row = (await session.execute(
        select(MPProfile.id, MPProfile.terms).where(MPProfile.prs_slug == slug)
    )).first()

    if profile_row is None:
        raise HTTPException(status_code=404, detail="MP not found")
    profile_id, terms = profile_row

    affidavit = (await session.execute(
        select(MpAffidavit)
        .options(
            selectinload(MpAffidavit.criminal_cases),
            selectinload(MpAffidavit.asset_history),
        )
        .where(MpAffidavit.mp_id == profile_id)
    )).scalar_one_or_none()

    if affidavit is None:
        raise HTTPException(status_code=404, detail="Integrity data not yet scraped for this MP")

    _hist = [(h.election_label, h.declared_assets) for h in affidavit.asset_history]

    return {
        "candidate_name": affidavit.candidate_name,
        "match_confidence": affidavit.match_confidence,
        "criminal": {
            "total_cases": affidavit.total_criminal_cases,
            "total_convictions": affidavit.total_convictions,
            "convictions_serious": affidavit.convictions_serious,
            "convictions_minor": max((affidavit.total_convictions or 0) - (affidavit.convictions_serious or 0), 0),
            "has_serious_cases": affidavit.has_serious_cases,
            "has_conviction": affidavit.has_conviction,
            "cases": [
                {
                    "ipc_section": c.ipc_section,
                    "description": c.description,
                    "is_serious": c.is_serious,
                }
                for c in affidavit.criminal_cases
            ],
        },
        "assets": {
            "total_assets": affidavit.total_assets,
            "total_liabilities": affidavit.total_liabilities,
            "movable_assets": affidavit.movable_assets,
            "immovable_assets": affidavit.immovable_assets,
            "self_income": affidavit.self_income,
            "spouse_income": affidavit.spouse_income,
            "growth": asset_growth(
                affidavit.total_assets, _hist,
            ) if (terms or 0) > 1 else None,
            "growth_first": asset_growth_first(
                affidavit.total_assets, _hist,
            ) if (terms or 0) > 1 else None,
            "series": asset_series(affidavit.total_assets, _hist) if (terms or 0) > 1 else [],
            "history": [
                {
                    "election": h.election_label,
                    "assets_rupees": h.declared_assets,
                }
                for h in affidavit.asset_history
            ],
        },
        "education": affidavit.education,
        "scraped_at": affidavit.scraped_at,
        "disclaimer": DISCLAIMER,
    }
