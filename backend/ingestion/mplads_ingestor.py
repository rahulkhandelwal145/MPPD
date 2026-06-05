"""Phase 3 — MPLADS ingestion.

Standalone module: reads the static MPLADS CSV, cleans MP names, matches them
to existing ``mp_profiles`` (rapidfuzz, same pattern as Phase 2), computes three
peer-relative percentile scores plus a weighted combined score, and upserts the
result into ``mp_mplads``.

Trigger once from the project root:

    .venv311\\Scripts\\python.exe -m backend.ingestion.mplads_ingestor

or programmatically::

    from backend.ingestion.mplads_ingestor import run
    print(run())

Re-run only when a newer CSV arrives — the upsert key is ``mp_name_raw``, so
re-ingesting overwrites rows in place rather than duplicating them.
"""
import asyncio
from pathlib import Path

import pandas as pd
from loguru import logger
from rapidfuzz import fuzz, process
from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.postgresql import insert as pg_insert

from backend.db.models import Base, MpMplads, MPProfile
from backend.db.session import AsyncSessionLocal, engine

# backend/ingestion/mplads_ingestor.py → parents[1] = backend, parents[2] = root
_BACKEND_DIR = Path(__file__).resolve().parents[1]
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = _BACKEND_DIR / "data" / "mplads.csv"
UNMATCHED_LOG = _PROJECT_ROOT / "data" / "mplads_unmatched.log"

MPLADS_WEIGHTS = {
    "utilization": 0.40,
    "completion": 0.40,
    "payment": 0.20,
}


# ─── Name cleaning ──────────────────────────────────────────────────────────────

PREFIXES_TO_STRIP = [
    "shri", "smt", "dr", "dr.", "prof", "prof.",
    "adv", "adv.", "col", "col.", "lt", "gen",
    "capt", "mr", "mrs", "ms", "er",
]


def clean_mp_name(name: str) -> str:
    """Collapse whitespace and strip a single leading honorific, then Title-Case."""
    name = " ".join(str(name).strip().split())
    lower = name.lower()
    for prefix in PREFIXES_TO_STRIP:
        if lower.startswith(prefix + " "):
            name = name[len(prefix):].strip()
            break  # only strip one prefix
    return name.title()


# ─── Name matching ──────────────────────────────────────────────────────────────

def log_unmatched(name: str, best_match: str | None, score: float) -> None:
    UNMATCHED_LOG.parent.mkdir(parents=True, exist_ok=True)
    with UNMATCHED_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{name} | {best_match} | {score}\n")


def match_to_profile(
    cleaned_name: str,
    profiles: list[dict],  # [{id, name}] from mp_profiles
) -> tuple[int | None, str]:
    """Returns (mp_id, confidence). confidence ∈ {exact, high, low, none}."""
    # Step 1: exact match (case-insensitive)
    target = cleaned_name.lower().strip()
    for p in profiles:
        if p["name"].lower().strip() == target:
            return p["id"], "exact"

    # Step 2: fuzzy match
    names = [p["name"] for p in profiles]
    result = process.extractOne(cleaned_name, names, scorer=fuzz.token_sort_ratio)
    if result is None:
        log_unmatched(cleaned_name, None, 0)
        return None, "none"

    match_name, score, idx = result
    if score >= 85:
        return profiles[idx]["id"], "high"
    elif score >= 70:
        log_unmatched(cleaned_name, match_name, score)
        return profiles[idx]["id"], "low"
    else:
        log_unmatched(cleaned_name, match_name, score)
        return None, "none"


# ─── Scoring ────────────────────────────────────────────────────────────────────

def mplads_combined_score(
    util: int | None,
    completion: int | None,
    payment: int | None,
) -> int | None:
    """Weighted average of the active sub-scores; NULL weight is redistributed."""
    scores = {"utilization": util, "completion": completion, "payment": payment}
    active = {k: v for k, v in scores.items() if v is not None}
    if not active:
        return None
    total_weight = sum(MPLADS_WEIGHTS[k] for k in active)
    weighted_sum = sum(active[k] * MPLADS_WEIGHTS[k] for k in active)
    return round(weighted_sum / total_weight)


def safe_int(val) -> int | None:
    try:
        f = float(val)
        return None if pd.isna(f) else int(f)
    except (ValueError, TypeError):
        return None


def safe_float(val) -> float | None:
    try:
        f = float(val)
        return None if pd.isna(f) else round(f, 2)
    except (ValueError, TypeError):
        return None


def canonicalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Map headers to canonical names regardless of the ₹ glyph's encoding.

    The source CSV is exported with a mojibaked rupee sign (``â¹``) in the amount
    headers, so we match the two amount columns by their text prefix instead of
    an exact ``₹`` match. Everything else keeps its (whitespace-stripped) name."""
    rename = {}
    for col in df.columns:
        c = str(col).strip()
        if c.startswith("Allocated Amount"):
            rename[col] = "Allocated Amount (₹)"
        elif c.startswith("Total Expenditure"):
            rename[col] = "Total Expenditure (₹)"
        else:
            rename[col] = c
    return df.rename(columns=rename)


def compute_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Adds utilization_score / completion_score / payment_score / mplads_score.

    Each sub-score is a percentile rank (0–100) computed *only* over the rows
    where the metric is defined, so excluded MPs don't dilute the peer pool.
    """
    # Edge-case masks: rows where a metric is undefined → that sub-score is NULL.
    allocated_zero = df["Allocated Amount (₹)"].astype(float) == 0
    no_works = df["Recommended Works"].astype(float) == 0
    no_transactions = df["Transaction Count"].astype(float) == 0

    # Sub-score 1: utilization (skip MPs with zero allocation — undefined %)
    mask_util = ~allocated_zero
    df.loc[mask_util, "utilization_score"] = (
        df.loc[mask_util, "Utilization %"].rank(method="min", pct=True) * 100
    ).round(0).astype(int)
    df.loc[~mask_util, "utilization_score"] = None

    # Sub-score 2: completion (skip MPs with no recommended works)
    mask_comp = ~no_works
    df.loc[mask_comp, "completion_score"] = (
        df.loc[mask_comp, "Completion Rate %"].rank(method="min", pct=True) * 100
    ).round(0).astype(int)
    df.loc[~mask_comp, "completion_score"] = None

    # Sub-score 3: payment efficiency = successful / total transactions
    mask_pay = ~no_transactions
    df.loc[mask_pay, "payment_efficiency"] = (
        df.loc[mask_pay, "Successful Payments"]
        / df.loc[mask_pay, "Transaction Count"] * 100
    )
    df.loc[mask_pay, "payment_score"] = (
        df.loc[mask_pay, "payment_efficiency"].rank(method="min", pct=True) * 100
    ).round(0).astype(int)
    df.loc[~mask_pay, "payment_score"] = None

    # Combined weighted score
    df["mplads_score"] = df.apply(
        lambda r: mplads_combined_score(
            safe_int(r.get("utilization_score")),
            safe_int(r.get("completion_score")),
            safe_int(r.get("payment_score")),
        ),
        axis=1,
    )
    return df


# ─── DB helpers ─────────────────────────────────────────────────────────────────

async def _ensure_table() -> None:
    """Create mp_mplads if it doesn't exist (idempotent; leaves other tables)."""
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: MpMplads.__table__.create(sync_conn, checkfirst=True)
        )


async def _fetch_all_profiles() -> list[dict]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(MPProfile.id, MPProfile.name))
        return [{"id": row.id, "name": row.name} for row in result.all()]


async def _upsert_records(records: list[dict]) -> None:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            dialect = session.bind.dialect.name
            for record in records:
                if dialect == "mysql":
                    stmt = mysql_insert(MpMplads).values(**record)
                    stmt = stmt.on_duplicate_key_update(**{
                        k: getattr(stmt.inserted, k)
                        for k in record
                        if k != "mp_name_raw"
                    })
                else:
                    stmt = pg_insert(MpMplads).values(**record)
                    stmt = stmt.on_conflict_do_update(
                        index_elements=[MpMplads.mp_name_raw],
                        set_={k: stmt.excluded[k] for k in record if k != "mp_name_raw"},
                    )
                await session.execute(stmt)


# ─── Pipeline ───────────────────────────────────────────────────────────────────

async def _run(csv_path: Path | str = CSV_PATH) -> dict:
    logger.info("Starting MPLADS ingestion")

    df = pd.read_csv(csv_path)
    df = canonicalize_columns(df)
    logger.info(f"Loaded {len(df)} rows from {csv_path}")

    df = compute_scores(df)
    df["name_clean"] = df["MP Name"].apply(clean_mp_name)

    await _ensure_table()
    profiles = await _fetch_all_profiles()
    logger.info(f"Matching against {len(profiles)} profiles")

    records, failed = [], []
    for _, row in df.iterrows():
        try:
            mp_id, confidence = match_to_profile(row["name_clean"], profiles)
            records.append({
                "mp_id": mp_id,
                "mp_name_raw": str(row["MP Name"]).strip(),
                "constituency": str(row["Constituency"]).strip() if pd.notna(row["Constituency"]) else None,
                "state": str(row["State"]).strip() if pd.notna(row["State"]) else None,
                "match_confidence": confidence,
                "allocated_amount": safe_int(row["Allocated Amount (₹)"]),
                "total_expenditure": safe_int(row["Total Expenditure (₹)"]),
                "utilization_pct": safe_float(row["Utilization %"]),
                "completed_works": safe_int(row["Completed Works"]),
                "recommended_works": safe_int(row["Recommended Works"]),
                "completion_rate_pct": safe_float(row["Completion Rate %"]),
                "transaction_count": safe_int(row["Transaction Count"]),
                "successful_payments": safe_int(row["Successful Payments"]),
                "pending_payments": safe_int(row["Pending Payments"]),
                "utilization_score": safe_int(row.get("utilization_score")),
                "completion_score": safe_int(row.get("completion_score")),
                "payment_score": safe_int(row.get("payment_score")),
                "mplads_score": safe_int(row.get("mplads_score")),
            })
        except Exception as e:  # noqa: BLE001 — one bad row shouldn't abort the run
            failed.append({"name": str(row.get("MP Name", "unknown")), "error": str(e)})
            logger.error(f"Failed {row.get('MP Name')}: {e}")

    await _upsert_records(records)

    logger.info(f"Done. Upserted: {len(records)} Failed: {len(failed)}")
    return {"upserted": len(records), "failed": failed}


def run(csv_path: Path | str = CSV_PATH) -> dict:
    """Synchronous entry point — runs the async pipeline to completion."""
    return asyncio.run(_run(csv_path))


if __name__ == "__main__":
    print(run())
