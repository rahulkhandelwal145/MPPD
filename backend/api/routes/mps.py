from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, case, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas import MPSummary, MPDetail, StatsSummary
from backend.core.assets import asset_growth, asset_growth_first, asset_series
from backend.core.scoring import compute_clean_record_score
from backend.db.models import MPProfile, MPScore, MPRawData, MpAffidavit, MpAssetHistory, PipelineRun
from backend.db.session import get_session

router = APIRouter(prefix="/mps", tags=["mps"])

CROREPATI_THRESHOLD = 10_000_000  # ₹1 crore


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


@router.get("/states", response_model=list[str])
async def list_states(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(MPProfile.state)
        .where(MPProfile.state.isnot(None), MPProfile.state != "")
        .distinct()
        .order_by(MPProfile.state)
    )
    return [row[0] for row in result.all()]


def _affidavit_aggregate():
    """One row per mp_id with integrity summary — joined into the list query so
    we can both filter/sort by it and surface it on cards."""
    return (
        select(
            MpAffidavit.mp_id.label("mp_id"),
            func.max(MpAffidavit.total_criminal_cases).label("criminal_cases"),
            func.max(MpAffidavit.total_convictions).label("convictions"),
            func.max(MpAffidavit.convictions_serious).label("convictions_serious"),
            func.max(MpAffidavit.total_assets).label("total_assets"),
            func.max(case((MpAffidavit.has_serious_cases, 1), else_=0)).label("serious"),
        )
        .where(MpAffidavit.mp_id.isnot(None))
        .group_by(MpAffidavit.mp_id)
        .subquery()
    )


async def _asset_growth_map(session: AsyncSession, mp_ids: list[int]) -> dict[int, dict]:
    """{mp_id: asset_growth(...)} for the given MPs. One scan of their affidavits
    + asset history, computed in Python (election labels are free-text, so the
    'most recent prior election' can't be picked in SQL)."""
    if not mp_ids:
        return {}
    aff_rows = (await session.execute(
        select(MpAffidavit.id, MpAffidavit.mp_id, MpAffidavit.total_assets)
        .where(MpAffidavit.mp_id.in_(mp_ids))
    )).all()
    aff_to_mp = {r.id: r.mp_id for r in aff_rows}
    current = {r.mp_id: r.total_assets for r in aff_rows}

    hist_by_mp: dict[int, list] = {}
    if aff_to_mp:
        hist_rows = (await session.execute(
            select(MpAssetHistory.affidavit_id, MpAssetHistory.election_label, MpAssetHistory.declared_assets)
            .where(MpAssetHistory.affidavit_id.in_(aff_to_mp.keys()))
        )).all()
        for r in hist_rows:
            mp = aff_to_mp.get(r.affidavit_id)
            if mp is not None:
                hist_by_mp.setdefault(mp, []).append((r.election_label, r.declared_assets))

    out = {}
    for mp, total in current.items():
        hist = hist_by_mp.get(mp, [])
        g = asset_growth(total, hist)
        if g is None:
            continue  # first-time MP / no prior declaration
        first = asset_growth_first(total, hist)
        out[mp] = {
            "pct": g["pct"],
            "since": g["since"],
            "first_pct": first["pct"] if first else None,
            "first_since": first["since"] if first else None,
            # compact points for the sparkline; drop the verbose label
            "series": [{"year": p["year"], "assets": p["assets"]} for p in asset_series(total, hist)],
        }
    return out


def _summary_from_row(row, growth_map: dict[int, dict] | None = None) -> MPSummary:
    """Build an MPSummary (incl. the derived clean-record and total scores) from
    a list-query row. Shared by the SQL-sorted and Python-sorted code paths."""
    profile, score, criminal_cases, convictions, convictions_serious, total_assets, serious = row
    # Asset growth is only meaningful for returning MPs (a first-time MP has no
    # prior Lok Sabha declaration to compare against).
    growth = (growth_map or {}).get(profile.id) if (profile.terms or 0) > 1 else None
    clean = (
        compute_clean_record_score(
            convictions_serious or 0,
            max((convictions or 0) - (convictions_serious or 0), 0),
        )
        if convictions is not None
        else None
    )
    metrics = [
        score.attendance_score, score.questions_score,
        score.debates_score, score.pmb_score, clean,
    ]
    present = [m for m in metrics if m is not None]
    total = round(sum(present) / len(present), 1) if present else None
    return MPSummary(
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
        terms=profile.terms,
        image_url=profile.image_url,
        attendance_score=score.attendance_score,
        questions_score=score.questions_score,
        debates_score=score.debates_score,
        pmb_score=score.pmb_score,
        peer_group=score.peer_group,
        total_peers=score.total_peers,
        criminal_cases=criminal_cases,
        convictions=convictions,
        convictions_serious=convictions_serious,
        total_assets=total_assets,
        has_serious_cases=bool(serious) if serious is not None else None,
        clean_record_score=clean,
        total_score=total,
        asset_growth_pct=growth["pct"] if growth else None,
        asset_growth_since=growth["since"] if growth else None,
        asset_growth_first_pct=growth["first_pct"] if growth else None,
        asset_growth_first_since=growth["first_since"] if growth else None,
        asset_series=growth["series"] if growth else None,
    )


@router.get("", response_model=dict)
async def list_mps(
    party: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    gender: Optional[str] = Query(None),
    is_minister: Optional[bool] = Query(None),
    is_speaker: Optional[bool] = Query(None),
    is_loa: Optional[bool] = Query(None),
    terms: Optional[int] = Query(None, ge=1),
    terms_min: Optional[int] = Query(None, ge=1),
    has_criminal_cases: Optional[bool] = Query(None),
    has_serious_cases: Optional[bool] = Query(None),
    is_convicted: Optional[bool] = Query(None),
    is_crorepati: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    sort: Optional[str] = Query(
        None,
        regex="^(attendance_score|questions_score|debates_score|pmb_score|total_score|total_assets|total_criminal_cases)$",
    ),
    direction: str = Query("desc", regex="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    latest_scores = await get_latest_scores(session)
    aff = _affidavit_aggregate()

    query = (
        select(MPProfile, MPScore, aff.c.criminal_cases, aff.c.convictions, aff.c.convictions_serious, aff.c.total_assets, aff.c.serious)
        .join(latest_scores, MPProfile.id == latest_scores.c.mp_id)
        .join(MPScore, and_(MPScore.mp_id == MPProfile.id, MPScore.scored_at == latest_scores.c.max_scored_at))
        .outerjoin(aff, aff.c.mp_id == MPProfile.id)
    )

    if party is not None:
        query = query.where(MPProfile.party == party)
    if state is not None:
        query = query.where(MPProfile.state == state)
    if gender is not None:
        query = query.where(MPProfile.gender == gender)
    if is_minister is not None:
        query = query.where(MPProfile.is_minister == is_minister)
    if is_speaker is not None:
        query = query.where(MPProfile.is_speaker == is_speaker)
    if is_loa is not None:
        query = query.where(MPProfile.is_loa == is_loa)
    if terms is not None:
        query = query.where(MPProfile.terms == terms)
    if terms_min is not None:
        query = query.where(MPProfile.terms >= terms_min)
    # Integrity filters (against the joined affidavit aggregate)
    if has_criminal_cases:
        query = query.where(aff.c.criminal_cases > 0)
    if has_serious_cases:
        query = query.where(aff.c.serious == 1)
    if is_convicted:
        query = query.where(aff.c.convictions > 0)
    if is_crorepati:
        query = query.where(aff.c.total_assets >= CROREPATI_THRESHOLD)
    if search:
        term = f"%{search}%"
        query = query.where(
            MPProfile.name.ilike(term) | MPProfile.constituency.ilike(term)
        )

    sort_columns = {
        "attendance_score": MPScore.attendance_score,
        "questions_score": MPScore.questions_score,
        "debates_score": MPScore.debates_score,
        "pmb_score": MPScore.pmb_score,
        "total_assets": aff.c.total_assets,
        "total_criminal_cases": aff.c.criminal_cases,
    }
    # "total_score" is the mean of an MP's available 0–100 metrics (incl. the
    # clean-record score, which is derived in Python). It can't be expressed as
    # a single SQL column, so we sort & paginate it in-process — the dataset is
    # small (~550 rows), so this is cheap. MPs with no scored metrics sort last.
    if sort == "total_score":
        rows = (await session.execute(query)).all()
        growth_map = await _asset_growth_map(session, [r[0].id for r in rows])
        summaries = [_summary_from_row(r, growth_map) for r in rows]
        reverse = direction == "desc"
        sentinel = float("-inf") if reverse else float("inf")
        summaries.sort(
            key=lambda s: s.total_score if s.total_score is not None else sentinel,
            reverse=reverse,
        )
        total = len(summaries)
        start = (page - 1) * limit
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "results": summaries[start : start + limit],
        }

    if sort:
        column = sort_columns[sort]
        query = query.order_by(column.desc() if direction == "desc" else column.asc())
    else:
        query = query.order_by(MPProfile.name.asc())

    total = await session.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * limit).limit(limit)
    rows = (await session.execute(query)).all()
    growth_map = await _asset_growth_map(session, [r[0].id for r in rows])

    return {
        "total": total or 0,
        "page": page,
        "limit": limit,
        "results": [_summary_from_row(r, growth_map) for r in rows],
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
            is_loa=profile.is_loa,
            age=profile.age,
            gender=profile.gender,
            education=profile.education,
            terms=profile.terms,
            image_url=profile.image_url,
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
        is_loa=profile.is_loa,
        age=profile.age,
        gender=profile.gender,
        education=profile.education,
        terms=profile.terms,
        image_url=profile.image_url,
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
