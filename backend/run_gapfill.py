"""Gap-fill: resolve MPs missing MyNeta integrity data via MyNeta's global
search (they were analyzed but absent from the 485-winner index page).

For each profile with no affidavit: search MyNeta -> pick best-name LokSabha2024
result -> verify constituency -> extract (Ollama) -> store linked directly to
the known profile. Conservative: skips low-confidence / constituency-mismatch /
candidate-ids already owned by another affidavit.

Usage from project root:
    .venv311\\Scripts\\python.exe -m backend.run_gapfill --dry      # resolve only, no writes
    .venv311\\Scripts\\python.exe -m backend.run_gapfill            # full run
"""
import asyncio
import sys
import time

import backend.core.config as cfg
cfg.settings.debug = False  # silence SQL echo

from rapidfuzz import fuzz  # noqa: E402
from sqlalchemy import text  # noqa: E402

from backend.agents.extraction_agent import extract_affidavit  # noqa: E402
from backend.agents.myneta_pipeline import _name_score, _normalize_name, _store_affidavit  # noqa: E402
from backend.db.session import AsyncSessionLocal  # noqa: E402
from backend.scraper.myneta import (  # noqa: E402
    CANDIDATE_URL,
    count_convictions,
    count_serious_convictions,
    fetch_with_cache,
    html_to_text,
    search_ls2024_candidates,
)

NAME_ACCEPT = 92      # accept on name alone at/above this
NAME_MIN = 80         # below this -> treat as not found


async def run(dry: bool = False) -> None:
    async with AsyncSessionLocal() as s:
        missing = (await s.execute(text(
            "SELECT p.id,p.name,p.constituency,p.state,p.party FROM mp_profiles p "
            "WHERE NOT EXISTS(SELECT 1 FROM mp_affidavits a WHERE a.mp_id=p.id) "
            "ORDER BY p.name"
        ))).all()
        existing = set((await s.execute(text(
            "SELECT myneta_candidate_id FROM mp_affidavits"
        ))).scalars().all())

    stats = dict(stored=0, notfound=0, conflict=0, cons_mismatch=0, extract_fail=0)
    for p in missing:
        try:
            cands = search_ls2024_candidates(p.name)
        except Exception as e:
            print(f"  SEARCH-ERR {p.name!r}: {str(e)[:50]}")
            stats["notfound"] += 1
            continue

        qn = _normalize_name(p.name)
        best, score = None, 0.0
        for cid, disp in cands:
            sc = _name_score(qn, _normalize_name(disp))
            if sc > score:
                best, score = (cid, disp), sc

        if best is None or score < NAME_MIN:
            print(f"  NOT-FOUND  {p.name!r} (best {score:.0f})")
            stats["notfound"] += 1
            continue

        cid, disp = best
        if cid in existing:
            print(f"  CONFLICT   {p.name!r} -> cid {cid} already owned by another affidavit")
            stats["conflict"] += 1
            continue

        html = fetch_with_cache(CANDIDATE_URL.format(id=cid), f"candidate_{cid}")
        page = html_to_text(html)
        cons_ok = (not p.constituency) or (_normalize_name(p.constituency) in _normalize_name(page))
        # Accept on name alone only for a near-full-string match (despaced),
        # not a bare subset like "Akshay" ⊂ "Akshay Yadav".
        despaced = fuzz.ratio(qn.replace(" ", ""), _normalize_name(disp).replace(" ", ""))
        if not cons_ok and despaced < NAME_ACCEPT:
            print(f"  CONS-MISS  {p.name!r} -> {disp!r} (name {score:.0f}, despaced {despaced:.0f}, constituency not on page)")
            stats["cons_mismatch"] += 1
            continue

        if dry:
            print(f"  WOULD-ADD  {p.name!r} -> cid {cid} {disp!r} (name {score:.0f}, cons_ok={cons_ok})")
            stats["stored"] += 1
            existing.add(cid)
            continue

        extraction = extract_affidavit(page, cid)
        conv = count_convictions(html)
        conv_serious = count_serious_convictions(html)
        if extraction is None:
            stats["extract_fail"] += 1
        await _store_affidavit(
            candidate={"candidate_id": cid, "name": p.name, "constituency": p.constituency,
                       "state": p.state, "party": p.party},
            extraction=extraction, mp_id=p.id, confidence="search",
            best_match_name=p.name, best_match_score=score, convictions=conv,
            convictions_serious=conv_serious,
        )
        existing.add(cid)
        stats["stored"] += 1
        print(f"  ADDED      {p.name!r} -> cid {cid} (conv={conv}, extract={'ok' if extraction else 'FAIL'})")
        time.sleep(1.0)

    print(f"\nmissing processed: {len(missing)} | {stats}")


if __name__ == "__main__":
    asyncio.run(run(dry="--dry" in sys.argv))
