import re
import time
from datetime import datetime
from pathlib import Path

from loguru import logger
from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.postgresql import insert as pg_insert

from backend.agents.extraction_agent import extract_affidavit
from backend.core.config import settings
from backend.db.models import MpAffidavit, MpAssetHistory, MpCriminalCase, MPProfile, PipelineRun
from backend.db.session import AsyncSessionLocal


def _trunc(value: str | None, limit: int) -> str | None:
    """Clamp a string to a column's length so a single bad extraction can't
    abort the row with a 'Data too long' DataError."""
    if value is None:
        return None
    return value[:limit]
from backend.scraper.myneta import (
    CANDIDATE_URL,
    WINNERS_URL,
    count_convictions,
    count_serious_convictions,
    fetch_with_cache,
    html_to_text,
    parse_winners_index,
)

UNMATCHED_LOG = Path("./data/unmatched_candidates.log")


# ─── DB helpers ────────────────────────────────────────────────────────────────

async def _create_pipeline_run() -> int:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            run = PipelineRun(status="running", mps_scraped=0, errors=[])
            session.add(run)
        await session.refresh(run)
        return run.id


async def _update_pipeline_run(
    run_id: int,
    status: str,
    scraped: int = 0,
    failed: list | None = None,
    error: str | None = None,
) -> None:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            run = await session.get(PipelineRun, run_id)
            if run is None:
                return
            run.status = status
            run.mps_scraped = scraped
            run.errors = failed or ([] if error is None else [{"reason": error}])
            run.completed_at = datetime.utcnow()
            session.add(run)


async def _get_all_profiles() -> list[dict]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(MPProfile.id, MPProfile.name))
        return [{"id": row.id, "name": row.name} for row in result.all()]


async def _store_affidavit(
    candidate: dict,
    extraction,
    mp_id: int | None,
    confidence: str,
    best_match_name: str | None,
    best_match_score: float | None,
    convictions: int = 0,
    convictions_serious: int = 0,
) -> None:
    cid = candidate["candidate_id"]
    success = extraction is not None

    values = {
        "mp_id": mp_id,
        "myneta_candidate_id": cid,
        "candidate_name": _trunc(candidate.get("name"), 200),
        "constituency": _trunc(candidate.get("constituency"), 200),
        "state": _trunc(candidate.get("state"), 100),
        "party": _trunc(candidate.get("party"), 100),
        "match_confidence": confidence,
        "best_match_name": _trunc(best_match_name, 200),
        "best_match_score": best_match_score,
        "total_criminal_cases": extraction.total_criminal_cases if success else 0,
        "total_convictions": convictions,
        "convictions_serious": convictions_serious,
        "has_serious_cases": any(c.is_serious for c in extraction.criminal_cases) if success else False,
        # Conviction count is parsed directly from the page's "Cases where
        # Convicted" table — more reliable than the LLM's has_conviction guess.
        "has_conviction": convictions > 0,
        "total_assets": extraction.total_assets_rupees if success else None,
        "movable_assets": extraction.movable_assets_rupees if success else None,
        "immovable_assets": extraction.immovable_assets_rupees if success else None,
        "total_liabilities": extraction.total_liabilities_rupees if success else None,
        "self_income": extraction.self_income_rupees if success else None,
        "spouse_income": extraction.spouse_income_rupees if success else None,
        "education": _trunc(extraction.education, 300) if success else None,
        "extraction_success": success,
    }

    async with AsyncSessionLocal() as session:
        async with session.begin():
            dialect = session.bind.dialect.name

            if dialect == "mysql":
                stmt = mysql_insert(MpAffidavit).values(**values)
                stmt = stmt.on_duplicate_key_update(**{
                    k: getattr(stmt.inserted, k)
                    for k in values
                    if k != "myneta_candidate_id"
                })
                await session.execute(stmt)
                await session.flush()
                affidavit_id = await session.scalar(
                    select(MpAffidavit.id).where(
                        MpAffidavit.myneta_candidate_id == cid
                    )
                )
            else:
                stmt = pg_insert(MpAffidavit).values(**values)
                stmt = stmt.on_conflict_do_update(
                    index_elements=[MpAffidavit.myneta_candidate_id],
                    set_={k: stmt.excluded[k] for k in values if k != "myneta_candidate_id"},
                ).returning(MpAffidavit.id)
                result = await session.execute(stmt)
                affidavit_id = result.scalar_one()

            if success and affidavit_id:
                # Delete stale child rows before re-inserting
                from sqlalchemy import delete
                await session.execute(
                    delete(MpCriminalCase).where(MpCriminalCase.affidavit_id == affidavit_id)
                )
                await session.execute(
                    delete(MpAssetHistory).where(MpAssetHistory.affidavit_id == affidavit_id)
                )

                for case in extraction.criminal_cases:
                    session.add(MpCriminalCase(
                        affidavit_id=affidavit_id,
                        ipc_section=_trunc(case.ipc_section, 100),
                        description=case.description,
                        is_serious=case.is_serious,
                        # These are pending charges, not convictions (convictions
                        # live in a separate MyNeta table, counted separately).
                        is_conviction=False,
                    ))

                for entry in extraction.asset_history:
                    session.add(MpAssetHistory(
                        affidavit_id=affidavit_id,
                        election_label=entry.election,
                        declared_assets=entry.assets_rupees,
                    ))


# ─── Name matching ─────────────────────────────────────────────────────────────

def _log_unmatched(name: str, best_match: str | None, score: float) -> None:
    UNMATCHED_LOG.parent.mkdir(parents=True, exist_ok=True)
    with UNMATCHED_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{name} | {best_match} | {score}\n")


_HONORIFIC_RE = re.compile(r"\b(dr|adv|advocate|smt|shri|capt|captain|prof)\.?\b")


def _normalize_name(name: str) -> str:
    """Strip parentheticals, aliases, 'S/O ...', honorifics and punctuation so
    name variants (initials, fuller middle names, alias suffixes) align."""
    n = name.lower()
    n = re.sub(r"\(.*?\)", "", n)        # (H.S.Patel)
    n = re.sub(r"\bs/o\b.*", "", n)      # S/O Ramdhar Prasad Mishra
    n = re.sub(r"\balias\b.*", "", n)    # Alias Pappu Yadav
    n = _HONORIFIC_RE.sub("", n)
    n = re.sub(r"[^a-z0-9 ]", " ", n)
    return re.sub(r"\s+", " ", n).strip()


def _name_score(a: str, b: str) -> float:
    """token_set handles subset names (Piyush Goyal ⊂ Piyush Vedprakash Goyal);
    despaced ratio handles spacing variants (Rajkumar Roat / Raj Kumar Roat)."""
    return max(
        fuzz.token_set_ratio(a, b),
        fuzz.ratio(a.replace(" ", ""), b.replace(" ", "")),
    )


def match_to_profile(
    candidate_name: str,
    profiles: list[dict],
) -> tuple[int | None, str, str | None, float | None]:
    """Returns (mp_id, confidence, best_match_name, best_match_score)."""
    # Exact match (case-insensitive)
    for p in profiles:
        if p["name"].lower().strip() == candidate_name.lower().strip():
            return p["id"], "exact", p["name"], 100.0

    # Fuzzy match on normalized names
    q = _normalize_name(candidate_name)
    best_score, best = 0.0, None
    for p in profiles:
        sc = _name_score(q, _normalize_name(p["name"]))
        if sc > best_score:
            best_score, best = sc, p

    if best is None:
        _log_unmatched(candidate_name, None, 0)
        return None, "none", None, None

    match_name = best["name"]
    if best_score >= 85:
        return best["id"], "high", match_name, float(best_score)
    elif best_score >= 70:
        _log_unmatched(candidate_name, match_name, best_score)
        return best["id"], "low", match_name, float(best_score)
    else:
        _log_unmatched(candidate_name, match_name, best_score)
        return None, "none", match_name, float(best_score)


# ─── Main pipeline ─────────────────────────────────────────────────────────────

async def run(force_refresh: bool = False) -> int:
    run_id = await _create_pipeline_run()

    try:
        logger.info("Fetching MyNeta winners index...")
        index_html = fetch_with_cache(
            url=WINNERS_URL,
            cache_key="winners_index",
            force=force_refresh,
        )
        candidates = parse_winners_index(index_html)
        logger.info(f"Found {len(candidates)} elected MPs")

        profiles = await _get_all_profiles()
        scraped, failed = 0, []

        for candidate in candidates:
            cid = candidate["candidate_id"]

            try:
                html = fetch_with_cache(
                    url=CANDIDATE_URL.format(id=cid),
                    cache_key=f"candidate_{cid}",
                    force=force_refresh,
                )

                page_text = html_to_text(html)
                extraction = extract_affidavit(page_text, cid)
                convictions = count_convictions(html)
                convictions_serious = count_serious_convictions(html)

                mp_id, confidence, best_match_name, best_match_score = match_to_profile(
                    candidate["name"], profiles
                )

                await _store_affidavit(
                    candidate=candidate,
                    extraction=extraction,
                    mp_id=mp_id,
                    confidence=confidence,
                    best_match_name=best_match_name,
                    best_match_score=best_match_score,
                    convictions=convictions,
                    convictions_serious=convictions_serious,
                )

                scraped += 1
                # Delay only matters for Groq's rate limit or live network fetches;
                # a local Ollama run from cache needs no throttle.
                if force_refresh or settings.llm_provider == "groq":
                    time.sleep(settings.scraper_delay_seconds)

            except Exception as e:
                failed.append({
                    "candidate_id": cid,
                    "name": candidate.get("name", "unknown"),
                    "reason": str(e),
                })
                logger.error(f"Failed candidate {cid}: {e}")

        await _update_pipeline_run(
            run_id=run_id,
            status="complete",
            scraped=scraped,
            failed=failed,
        )
        logger.info(f"MyNeta pipeline complete: {scraped} scraped, {len(failed)} failed")

    except Exception as e:
        await _update_pipeline_run(run_id=run_id, status="failed", error=str(e))
        logger.error(f"MyNeta pipeline failed: {e}")

    return run_id
