from loguru import logger
from rapidfuzz import process

from backend.core.config import settings


def _normalize_name(name: str) -> str:
    return name.strip().lower().replace("  ", " ")


def _match_name(name: str, candidates: list[str]) -> str | None:
    if not candidates:
        return None
    match = process.extractOne(name, candidates, score_cutoff=80)
    if match:
        return match[0]
    return None


def _fetch_mplads_records() -> list[dict]:
    try:
        from datagovindia import DataGov
    except ImportError:
        logger.warning("datagovindia package is not installed; MPLADS data will be skipped")
        return []

    if not settings.datagov_api_key:
        logger.warning("DATAGOV_API_KEY is missing; skipping MPLADS data")
        return []

    try:
        client = DataGov(api_key=settings.datagov_api_key)
        result = client.search(resource_id="963eb2d0-1afa-4d25-8dfe-3f5c57b9289d", limit=500)
        return result.get("records", []) if isinstance(result, dict) else []
    except Exception as exc:
        logger.exception("Failed to fetch MPLADS records")
        return []


async def run_mplads_agent(run_id: int, mp_rows: list[dict]) -> dict:
    records = _fetch_mplads_records()
    if not records:
        return {"mplads_data": {}}

    candidates = [_normalize_name(row["name"]) for row in mp_rows if row.get("name")]
    slug_by_name = { _normalize_name(row["name"]): row["slug"] for row in mp_rows if row.get("name") }
    mplads_data: dict[str, float] = {}

    for record in records:
        name = record.get("mp_name") or record.get("name") or ""
        utilization = record.get("utilization_percentage") or record.get("utilization")
        if utilization is None:
            continue
        matched_name = _match_name(_normalize_name(name), candidates)
        if not matched_name:
            continue
        slug = slug_by_name.get(matched_name)
        try:
            value = float(utilization)
        except (TypeError, ValueError):
            continue
        if slug:
            mplads_data[slug] = value

    return {"mplads_data": mplads_data}
