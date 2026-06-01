from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, case, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas import MPSummary, MPDetail, StatsSummary
from backend.db.models import MPProfile, MPScore, MPRawData, PipelineRun
from backend.db.session import get_session

router = APIRouter(prefix="/mps", tags=["mps"])

SORT_FIELDS = {
    "attendance_score": MPScore.attendance_score,
    "questions_score": MPScore.questions_score,
    "debates_score": MPScore.debates_score,
    "pmb_score": MPScore.pmb_score,
}


async def get_latest_scores(session: AsyncSession):
    subq = select(
        MPScore.mp_id,
        func.max(MPScore.scored_at).label("max_scored_at"),
    ).group_by(MPScore.mp_id).subquery()
    return subq


@router.get("/parties", response_model=list[str])
async def list_parties(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(MPProfile.party)
        .where(MPProfile.party.isnot(None), MPProfile.party != "")
        .distinct()
        .order_by(MPProfile.party)
    )
    return [row[0] for row in result.all()]


@router.get("", response_model=dict)
async def list_mps(
    party: Optional[str] = Query(None),
    is_minister: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    sort: Optional[str] = Query(None, regex="^(attendance_score|questions_score|debates_score|pmb_score)$"),
    direction: str = Query("desc", regex="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    latest_scores = await get_latest_scores(session)
    score_alias = MPScore.__table__.alias("scores")

    query = (
        select(MPProfile, MPScore)
        .join(latest_scores, MPProfile.id == latest_scores.c.mp_id)
        .join(MPScore, and_(MPScore.mp_id == MPProfile.id, MPScore.scored_at == latest_scores.c.max_scored_at))
    )

    if party is not None:
        query = query.where(MPProfile.party == party)
    if is_minister is not None:
        query = query.where(MPProfile.is_minister == is_minister)
    if search:
        term = f"%{search}%"
        query = query.where(
            MPProfile.name.ilike(term) | MPProfile.constituency.ilike(term)
        )
    if sort:
        column = SORT_FIELDS[sort]
        query = query.order_by(column.desc() if direction == "desc" else column.asc())
    else:
        query = query.order_by(MPProfile.name.asc())

    total = await session.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * limit).limit(limit)
    result = await session.execute(query)
    rows = result.all()

    return {
        "total": total or 0,
        "page": page,
        "limit": limit,
        "results": [
            MPSummary(
                name=profile.name,
                prs_slug=profile.prs_slug,
                constituency=profile.constituency,
                state=profile.state,
                party=profile.party,
                is_minister=profile.is_minister,
                is_speaker=profile.is_speaker,
                is_loa=profile.is_loa,
                age=profile.age,
                gender=profile.gender,
                education=profile.education,
                attendance_score=score.attendance_score,
                questions_score=score.questions_score,
                debates_score=score.debates_score,
                pmb_score=score.pmb_score,
                peer_group=score.peer_group,
                total_peers=score.total_peers,
            )
            for profile, score in rows
        ],
    }


@router.get("/leaderboard", response_model=list[MPSummary])
async def leaderboard(
    metric: str = Query(..., regex="^(attendance|questions|debates|pmb)$"),
    direction: str = Query("top", regex="^(top|bottom)$"),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    field_map = {
        "attendance": MPScore.attendance_score,
        "questions": MPScore.questions_score,
        "debates": MPScore.debates_score,
        "pmb": MPScore.pmb_score,
    }
    column = field_map[metric]
    order = column.desc() if direction == "top" else column.asc()

    latest_scores = await get_latest_scores(session)
    query = (
        select(MPProfile, MPScore)
        .join(latest_scores, MPProfile.id == latest_scores.c.mp_id)
        .join(MPScore, and_(MPScore.mp_id == MPProfile.id, MPScore.scored_at == latest_scores.c.max_scored_at))
        .where(column.is_not(None))
        .order_by(order)
        .limit(limit)
    )
    result = await session.execute(query)
    return [
        MPSummary(
            name=profile.name,
            prs_slug=profile.prs_slug,
            constituency=profile.constituency,
            state=profile.state,
            party=profile.party,
            is_minister=profile.is_minister,
            is_speaker=profile.is_speaker,
            age=profile.age,
            gender=profile.gender,
            education=profile.education,
            attendance_score=score.attendance_score,
            questions_score=score.questions_score,
            debates_score=score.debates_score,
            pmb_score=score.pmb_score,
            peer_group=score.peer_group,
            total_peers=score.total_peers,
        )
        for profile, score in result.all()
    ]


@router.get("/stats/summary", response_model=StatsSummary)
async def stats_summary(session: AsyncSession = Depends(get_session)):
    latest_scores = await get_latest_scores(session)
    score_query = (
        select(
            func.count(MPProfile.id),
            func.count(case((MPProfile.is_minister, 1))),
            func.avg(MPScore.attendance_score),
            func.avg(MPScore.questions_score),
            func.avg(MPScore.debates_score),
            func.avg(MPScore.pmb_score),
        )
        .select_from(MPProfile)
        .join(latest_scores, MPProfile.id == latest_scores.c.mp_id)
        .join(MPScore, and_(MPScore.mp_id == MPProfile.id, MPScore.scored_at == latest_scores.c.max_scored_at))
    )
    result = await session.execute(score_query)
    row = result.one_or_none()
    total_mps = row[0] or 0
    total_ministers = row[1] or 0
    last_run = await session.execute(
        select(PipelineRun).order_by(PipelineRun.completed_at.desc()).limit(1)
    )
    last = last_run.scalar_one_or_none()

    return StatsSummary(
        total_mps=total_mps,
        total_ministers=total_ministers,
        last_run_at=last.completed_at if last else None,
        last_run_status=last.status if last else None,
        avg_attendance_score=row[2],
        avg_questions_score=row[3],
        avg_debates_score=row[4],
        avg_pmb_score=row[5],
    )


@router.get("/{slug}", response_model=MPDetail)
async def get_mp(slug: str, session: AsyncSession = Depends(get_session)):
    latest_scores = await get_latest_scores(session)
    query = (
        select(MPProfile, MPScore, MPRawData)
        .join(MPScore, MPScore.mp_id == MPProfile.id)
        .join(MPRawData, MPRawData.mp_id == MPProfile.id)
        .join(latest_scores, and_(MPScore.mp_id == latest_scores.c.mp_id, MPScore.scored_at == latest_scores.c.max_scored_at))
        .where(MPProfile.prs_slug == slug)
        .order_by(MPRawData.scraped_at.desc())
        .limit(1)
    )
    result = await session.execute(query)
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="MP not found")
    profile, score, raw = row
    return MPDetail(
        name=profile.name,
        prs_slug=profile.prs_slug,
        constituency=profile.constituency,
        state=profile.state,
        party=profile.party,
        is_minister=profile.is_minister,
        is_speaker=profile.is_speaker,
        age=profile.age,
        gender=profile.gender,
        education=profile.education,
        raw={
            "attendance_pct": raw.attendance_pct,
            "questions_count": raw.questions_count,
            "debates_count": raw.debates_count,
            "pmb_count": raw.pmb_count,
            "mplads_utilization": raw.mplads_utilization,
            "national_avg_attendance": raw.national_avg_attendance,
            "state_avg_attendance": raw.state_avg_attendance,
            "national_avg_questions": raw.national_avg_questions,
            "state_avg_questions": raw.state_avg_questions,
            "national_avg_debates": raw.national_avg_debates,
            "state_avg_debates": raw.state_avg_debates,
            "national_avg_pmb": raw.national_avg_pmb,
            "state_avg_pmb": raw.state_avg_pmb,
        },
        scores={
            "attendance_score": score.attendance_score,
            "questions_score": score.questions_score,
            "debates_score": score.debates_score,
            "pmb_score": score.pmb_score,
        },
        ranks={
            "attendance_rank": score.attendance_rank,
            "questions_rank": score.questions_rank,
            "debates_rank": score.debates_rank,
            "pmb_rank": score.pmb_rank,
            "total_peers": score.total_peers,
        },
        peer_group=score.peer_group,
        scored_at=score.scored_at,
    )
