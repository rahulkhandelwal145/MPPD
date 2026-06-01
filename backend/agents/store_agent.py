from datetime import datetime

from sqlalchemy import insert, select
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import MPProfile, MPRawData, MPScore, PipelineRun
from backend.db.session import AsyncSessionLocal


async def _upsert_profile(session: AsyncSession, row: dict) -> int:
    values = {
        "name": row["name"],
        "prs_slug": row["slug"],
        "constituency": row.get("constituency"),
        "state": row.get("state"),
        "party": row.get("party"),
        "age": row.get("age"),
        "gender": row.get("gender"),
        "education": row.get("education"),
        "is_minister": row.get("is_minister", False),
        "is_speaker": row.get("is_speaker", False),
    }
    dialect_name = session.bind.dialect.name

    if dialect_name == "mysql":
        stmt = mysql_insert(MPProfile).values(**values)
        stmt = stmt.on_duplicate_key_update(
            name=stmt.inserted.name,
            constituency=stmt.inserted.constituency,
            state=stmt.inserted.state,
            party=stmt.inserted.party,
            age=stmt.inserted.age,
            gender=stmt.inserted.gender,
            education=stmt.inserted.education,
            is_minister=stmt.inserted.is_minister,
            is_speaker=stmt.inserted.is_speaker,
            updated_at=datetime.utcnow(),
        )
        await session.execute(stmt)
        await session.flush()
        return await session.scalar(select(MPProfile.id).where(MPProfile.prs_slug == row["slug"]))

    stmt = pg_insert(MPProfile).values(**values)
    update_values = {
        "name": stmt.excluded.name,
        "constituency": stmt.excluded.constituency,
        "state": stmt.excluded.state,
        "party": stmt.excluded.party,
        "age": stmt.excluded.age,
        "gender": stmt.excluded.gender,
        "education": stmt.excluded.education,
        "is_minister": stmt.excluded.is_minister,
        "is_speaker": stmt.excluded.is_speaker,
        "updated_at": datetime.utcnow(),
    }
    stmt = stmt.on_conflict_do_update(index_elements=[MPProfile.prs_slug], set_=update_values).returning(MPProfile.id)
    result = await session.execute(stmt)
    return result.scalar_one()


async def store_pipeline_results(state: dict, run_id: int) -> None:
    raw_data = state.get("raw_mp_data", [])
    scored_data = state.get("scored_data", [])
    errors = state.get("errors", [])

    async with AsyncSessionLocal() as session:
        async with session.begin():
            profile_ids: dict[str, int] = {}
            for row in raw_data:
                slug = row["slug"]
                profile_ids[slug] = await _upsert_profile(session, row)

            mplads_map = state.get("mplads_data", {})
            for row in raw_data:
                mp_id = profile_ids[row["slug"]]
                raw_row = MPRawData(
                    mp_id=mp_id,
                    attendance_pct=row.get("attendance_pct"),
                    questions_count=row.get("questions_count"),
                    debates_count=row.get("debates_count"),
                    pmb_count=row.get("pmb_count"),
                    mplads_utilization=state.get("mplads_data", {}).get(row["slug"]),
                    national_avg_attendance=row.get("national_avg_attendance"),
                    state_avg_attendance=row.get("state_avg_attendance"),
                    national_avg_questions=row.get("national_avg_questions"),
                    state_avg_questions=row.get("state_avg_questions"),
                    national_avg_debates=row.get("national_avg_debates"),
                    state_avg_debates=row.get("state_avg_debates"),
                    national_avg_pmb=row.get("national_avg_pmb"),
                    state_avg_pmb=row.get("state_avg_pmb"),
                )
                session.add(raw_row)

            for row in scored_data:
                mp_id = profile_ids.get(row["slug"])
                if mp_id is None:
                    continue
                score_row = MPScore(
                    mp_id=mp_id,
                    peer_group=row["peer_group"],
                    attendance_score=row.get("attendance_score"),
                    questions_score=row.get("questions_score"),
                    debates_score=row.get("debates_score"),
                    pmb_score=row.get("pmb_score"),
                    attendance_rank=row.get("attendance_rank"),
                    questions_rank=row.get("questions_rank"),
                    debates_rank=row.get("debates_rank"),
                    pmb_rank=row.get("pmb_rank"),
                    total_peers=row.get("total_peers", 0),
                    scored_at=row.get("scored_at") or datetime.utcnow(),
                )
                session.add(score_row)

            pipeline = await session.get(PipelineRun, run_id)
            if pipeline is not None:
                pipeline.status = "failed" if errors else "complete"
                pipeline.mps_scraped = len(raw_data)
                pipeline.mps_scored = len(scored_data)
                pipeline.errors = errors or []
                pipeline.completed_at = datetime.utcnow()
                session.add(pipeline)
