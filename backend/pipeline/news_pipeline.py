"""Phase 4 — weekly news pipeline for the Public Statement Monitor.

Per MP: query Google News RSS -> keep whitelisted outlets -> fetch + clean
article text -> extract direct quotes (LLM) -> classify each quote (LLM) ->
store only non-E statements. Runs weekly via APScheduler, manually via
POST /api/v1/statements/run.

Display feature only — never contributes to any MP score.

DB access is async (matching the rest of the app); the network + LLM calls are
synchronous and run inline. This pipeline is meant to run as a background job
(scheduler thread / FastAPI BackgroundTask), not inside the API request loop.
"""

import asyncio
import time
from datetime import datetime, timedelta
from pathlib import Path

from loguru import logger
from sqlalchemy import delete, func, select

_LOG_FILE = Path(__file__).resolve().parents[2] / "logs" / "statement_monitor.log"
_LOG_FILE.parent.mkdir(exist_ok=True)
logger.add(_LOG_FILE, rotation="10 MB", retention=4, encoding="utf-8")

from backend.agents.statement_agent import classify_statement, extract_quotes
from backend.core.config import settings
from backend.db.models import MpNewsArticle, MpStatement, MPProfile, PipelineRun
from backend.db.session import AsyncSessionLocal
from backend.scraper.news import (
    clear_feed_cache,
    entry_source_domain,
    fetch_article,
    fetch_rss,
    filter_by_whitelist,
    html_to_text,
    parse_date,
    resolve_article_url,
    warm_feed_cache,
)

# How far back news is considered "current". Older entries are skipped.
LOOKBACK_DAYS = 30
MAX_ARTICLES_PER_MP = 10
ARTICLE_DELAY_SECONDS = 1.5
MP_DELAY_SECONDS = 2.0

# Status of the most recent run, surfaced by GET /statements/pipeline/status.
# Best-effort, in-process only.
_LAST_RUN: dict = {
    "last_run_at": None,
    "mps_processed": 0,
    "total_articles": 0,
    "total_flagged": 0,
    "errors": [],
    "running": False,
}


def _truncate(value: str | None, limit: int) -> str | None:
    if value is None:
        return None
    return value[:limit]


# ─── DB helpers ────────────────────────────────────────────────────────────────

async def fetch_all_profiles() -> list[dict]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(MPProfile.id, MPProfile.name, MPProfile.prs_slug)
        )
        return [{"id": r.id, "name": r.name, "slug": r.prs_slug} for r in result.all()]


async def article_exists(url: str) -> bool:
    async with AsyncSessionLocal() as session:
        existing = await session.scalar(
            select(MpNewsArticle.id).where(MpNewsArticle.url == url)
        )
        return existing is not None


async def store_article(
    mp_id: int,
    url: str,
    title: str | None,
    source_domain: str,
    published_at: datetime | None,
    article_text: str,
) -> int:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            article = MpNewsArticle(
                mp_id=mp_id,
                url=_truncate(url, 500),
                title=_truncate(title, 500),
                source_domain=_truncate(source_domain, 100),
                published_at=published_at,
                article_text=article_text,
            )
            session.add(article)
        await session.refresh(article)
        return article.id


async def mark_quotes_extracted(article_id: int) -> None:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            article = await session.get(MpNewsArticle, article_id)
            if article is not None:
                article.quotes_extracted = True


async def store_statement(
    mp_id: int,
    article_id: int,
    verbatim: str,
    context: str | None,
    classification: dict,
    source_domain: str,
    article_url: str,
    published_at: datetime | None,
) -> None:
    category = classification["category"]
    async with AsyncSessionLocal() as session:
        async with session.begin():
            session.add(MpStatement(
                mp_id=mp_id,
                article_id=article_id,
                verbatim=verbatim,
                context=context,
                category=category,
                category_group=category[0],
                constitutional_anchor=_truncate(classification.get("constitutional_anchor"), 200),
                data_contradicted=_truncate(classification.get("data_contradicted"), 200),
                reason=classification.get("reason"),
                confidence=classification.get("confidence"),
                source_domain=_truncate(source_domain, 100),
                article_url=_truncate(article_url, 500),
                published_at=published_at,
            ))


# ─── Per-MP processing ─────────────────────────────────────────────────────────

async def run_for_mp(mp: dict) -> dict:
    """Process one MP. Returns a stats dict."""
    articles_fetched = 0
    quotes_extracted = 0
    statements_stored = 0
    errors: list[str] = []

    cutoff = datetime.utcnow() - timedelta(days=LOOKBACK_DAYS)
    entries = filter_by_whitelist(fetch_rss(mp["name"]))

    for entry in entries:
        if articles_fetched >= MAX_ARTICLES_PER_MP:
            break
        try:
            domain = entry_source_domain(entry)

            # Resolve the real publisher URL. Google News RSS encodes the URL
            # as an opaque JavaScript-only redirect; we match it back to the
            # publisher's own RSS feed by title similarity.
            url = resolve_article_url(entry, mp["name"])
            if not url:
                logger.debug(f"No URL resolved for '{getattr(entry,'title','?')[:60]}'")
                continue

            published_at = parse_date(getattr(entry, "published_parsed", None))
            if published_at is not None and published_at < cutoff:
                continue

            if await article_exists(url):
                continue

            html = fetch_article(url)
            if not html:
                continue

            article_text = html_to_text(html)
            if len(article_text) < 200:
                continue

            article_id = await store_article(
                mp_id=mp["id"],
                url=url,
                title=getattr(entry, "title", None),
                source_domain=domain,
                published_at=published_at,
                article_text=article_text,
            )
            articles_fetched += 1

            quotes = extract_quotes(article_text, mp["name"])
            await mark_quotes_extracted(article_id)
            if not quotes:
                continue
            quotes_extracted += len(quotes)

            date_str = published_at.isoformat() if published_at else ""
            for quote in quotes:
                result = classify_statement(
                    statement=quote["text"],
                    context=quote.get("context", ""),
                    mp_name=mp["name"],
                    source=domain,
                    date=date_str,
                )
                if result is None:
                    continue

                # Only store flagged (A/B/C) and constructive (D). E is discarded.
                if result["category"] != "E":
                    await store_statement(
                        mp_id=mp["id"],
                        article_id=article_id,
                        verbatim=quote["text"],
                        context=quote.get("context", ""),
                        classification=result,
                        source_domain=domain,
                        article_url=url,
                        published_at=published_at,
                    )
                    statements_stored += 1

            time.sleep(ARTICLE_DELAY_SECONDS)

        except Exception as e:  # noqa: BLE001 — one bad article must not abort the MP
            errors.append(str(e))
            logger.error(f"Error processing article for {mp['name']}: {e}")
            continue

    return {
        "mp_name": mp["name"],
        "articles_fetched": articles_fetched,
        "quotes_extracted": quotes_extracted,
        "statements_stored": statements_stored,
        "errors": errors,
    }


# ─── Full run ──────────────────────────────────────────────────────────────────

async def _create_run() -> int:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            run = PipelineRun(status="running", mps_scraped=0, errors=[])
            session.add(run)
        await session.refresh(run)
        return run.id


async def _finish_run(run_id: int, status: str, processed: int, errors: list) -> None:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            run = await session.get(PipelineRun, run_id)
            if run is None:
                return
            run.status = status
            run.mps_scraped = processed
            run.errors = errors
            run.completed_at = datetime.utcnow()


async def run_all(
    limit: int | None = None,
    only_slug: str | None = None,
    offset: int = 0,
) -> dict:
    """Weekly job — process MPs sequentially.

    ``limit`` / ``offset`` / ``only_slug`` are test affordances for batched
    manual runs; the scheduled run passes none of them and processes every MP.
    """
    logger.info("Starting news pipeline run")
    _LAST_RUN.update(running=True, errors=[], mps_processed=0, total_articles=0, total_flagged=0)
    run_id = await _create_run()

    logger.info("Warming publisher RSS feed cache...")
    warm_feed_cache()
    logger.info("Publisher feeds cached.")

    mps = await fetch_all_profiles()
    if only_slug:
        mps = [m for m in mps if m["slug"] == only_slug]
    if offset:
        mps = mps[offset:]
    if limit:
        mps = mps[:limit]

    processed = 0
    total_articles = 0
    total_statements = 0
    errors: list = []

    try:
        for mp in mps:
            logger.info(f"Processing {mp['name']}")
            result = await run_for_mp(mp)
            processed += 1
            total_articles += result["articles_fetched"]
            total_statements += result["statements_stored"]
            if result["errors"]:
                errors.append({"mp": mp["name"], "errors": result["errors"]})

            _LAST_RUN.update(
                mps_processed=processed,
                total_articles=total_articles,
                total_flagged=total_statements,
            )
            logger.info(f"  Done: {result}")
            time.sleep(MP_DELAY_SECONDS)

        await _finish_run(run_id, "complete", processed, errors)
        logger.info(f"News pipeline complete: {processed} MPs, {total_articles} articles, {total_statements} statements")

    except Exception as e:  # noqa: BLE001
        await _finish_run(run_id, "failed", processed, errors + [{"fatal": str(e)}])
        logger.error(f"News pipeline failed: {e}")

    finally:
        _LAST_RUN.update(running=False, last_run_at=datetime.utcnow().isoformat())
        clear_feed_cache()

    return {
        "run_id": run_id,
        "mps_processed": processed,
        "total_articles": total_articles,
        "total_statements": total_statements,
    }


def run_all_sync(limit: int | None = None, only_slug: str | None = None, offset: int = 0) -> dict:
    """Blocking wrapper for the APScheduler (sync) job and BackgroundTasks."""
    return asyncio.run(run_all(limit=limit, only_slug=only_slug, offset=offset))


async def last_run_status() -> dict:
    """Status snapshot for GET /statements/pipeline/status, backed by live DB
    counts so it survives a process restart."""
    async with AsyncSessionLocal() as session:
        total_articles = await session.scalar(select(func.count(MpNewsArticle.id)))
        total_flagged = await session.scalar(
            select(func.count(MpStatement.id)).where(MpStatement.category_group.in_(["A", "B", "C"]))
        )
        last_run = (await session.execute(
            select(PipelineRun).order_by(PipelineRun.started_at.desc()).limit(1)
        )).scalar_one_or_none()

    return {
        "last_run_at": _LAST_RUN["last_run_at"]
        or (last_run.completed_at.isoformat() if last_run and last_run.completed_at else None),
        "running": _LAST_RUN["running"],
        "mps_processed": _LAST_RUN["mps_processed"] or (last_run.mps_scraped if last_run else 0),
        "total_articles": total_articles or 0,
        "total_flagged": total_flagged or 0,
        "errors": _LAST_RUN["errors"] or (last_run.errors if last_run else []),
    }
