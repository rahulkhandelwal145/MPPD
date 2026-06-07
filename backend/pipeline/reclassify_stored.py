"""One-time backfill: re-extract + re-classify statements from already-stored
article texts. Use this after changing the classification prompt or model.

Does NOT hit any news sites — reads article_text from mp_news_articles in DB.
Safe to run alongside the weekly pipeline since it never touches mp_news_articles.

Usage:
    .venv311\\Scripts\\python.exe -m backend.pipeline.reclassify_stored
    .venv311\\Scripts\\python.exe -m backend.pipeline.reclassify_stored --slug rahul-gandhi
    .venv311\\Scripts\\python.exe -m backend.pipeline.reclassify_stored --limit 10
"""

import argparse
import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path

from loguru import logger
from sqlalchemy import delete, select

_LOG_FILE = Path(__file__).resolve().parents[2] / "logs" / "reclassify.log"
_LOG_FILE.parent.mkdir(exist_ok=True)
logger.add(_LOG_FILE, rotation="10 MB", retention=3, encoding="utf-8")

from backend.agents.statement_agent import classify_statement, extract_quotes
from backend.db.models import MpNewsArticle, MpStatement, MPProfile
from backend.db.session import AsyncSessionLocal


def _truncate(value: str | None, limit: int) -> str | None:
    return value[:limit] if value else None


async def _fetch_articles(only_slug: str | None, limit: int | None) -> list[dict]:
    async with AsyncSessionLocal() as session:
        q = (
            select(
                MpNewsArticle.id,
                MpNewsArticle.mp_id,
                MpNewsArticle.url,
                MpNewsArticle.article_text,
                MpNewsArticle.source_domain,
                MpNewsArticle.published_at,
                MPProfile.name.label("mp_name"),
                MPProfile.prs_slug,
            )
            .join(MPProfile, MPProfile.id == MpNewsArticle.mp_id)
            .where(MpNewsArticle.article_text.isnot(None))
        )
        if only_slug:
            q = q.where(MPProfile.prs_slug == only_slug)
        if limit:
            q = q.limit(limit)
        rows = (await session.execute(q)).all()
    return [r._asdict() for r in rows]


async def _clear_statements(mp_ids: set[int] | None = None) -> int:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            if mp_ids:
                result = await session.execute(
                    delete(MpStatement).where(MpStatement.mp_id.in_(mp_ids))
                )
            else:
                result = await session.execute(delete(MpStatement))
        return result.rowcount


async def _store_statement(article: dict, verbatim: str, context: str, r: dict) -> None:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            session.add(MpStatement(
                mp_id=article["mp_id"],
                article_id=article["id"],
                verbatim=verbatim,
                context=context,
                category=r["category"],
                category_group=r["category"][0],
                constitutional_anchor=_truncate(r.get("constitutional_anchor"), 200),
                data_contradicted=_truncate(r.get("data_contradicted"), 200),
                reason=r.get("reason"),
                confidence=r.get("confidence"),
                source_domain=_truncate(article["source_domain"], 100),
                article_url=_truncate(article["url"], 500),
                published_at=article["published_at"],
            ))


async def run(only_slug: str | None = None, limit: int | None = None) -> dict:
    articles = await _fetch_articles(only_slug, limit)
    logger.info(f"Re-classifying {len(articles)} stored articles")

    mp_ids = {a["mp_id"] for a in articles}
    deleted = await _clear_statements(mp_ids if only_slug else None)
    logger.info(f"Cleared {deleted} existing statements for affected MPs")

    total_quotes = 0
    total_stored = 0
    errors = []

    for i, article in enumerate(articles, 1):
        mp_name = article["mp_name"]
        text = article["article_text"] or ""
        if len(text) < 200:
            continue

        logger.info(f"[{i}/{len(articles)}] {mp_name} | {article['source_domain']}")

        try:
            quotes = extract_quotes(text, mp_name)
            if not quotes:
                continue
            total_quotes += len(quotes)

            date_str = article["published_at"].isoformat() if article["published_at"] else ""
            for quote in quotes:
                result = classify_statement(
                    statement=quote["text"],
                    context=quote.get("context", ""),
                    mp_name=mp_name,
                    source=article["source_domain"] or "",
                    date=date_str,
                )
                if result is None or result["category"] == "E":
                    continue
                await _store_statement(article, quote["text"], quote.get("context", ""), result)
                total_stored += 1
                logger.info(f"  Stored [{result['category']}] conf={result['confidence']}%: {quote['text'][:80]}")

            time.sleep(1.0)

        except Exception as e:
            errors.append({"article_id": article["id"], "error": str(e)})
            logger.error(f"  Error on article {article['id']}: {e}")

    logger.info(f"Done: {len(articles)} articles, {total_quotes} quotes, {total_stored} statements stored")
    return {
        "articles_processed": len(articles),
        "quotes_extracted": total_quotes,
        "statements_stored": total_stored,
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Re-classify stored article texts")
    parser.add_argument("--slug", help="Limit to one MP slug")
    parser.add_argument("--limit", type=int, help="Max number of articles to process")
    args = parser.parse_args()
    result = asyncio.run(run(only_slug=args.slug, limit=args.limit))
    print(result)


if __name__ == "__main__":
    main()
