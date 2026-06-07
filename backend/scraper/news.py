"""Phase 4 — News scraper for the Public Statement Monitor.

Strategy: Google News RSS is used for discovery (excellent search quality,
free, no API key). The article URLs in Google News RSS are encrypted redirects
that only resolve via JavaScript — they are decoded via the ``googlenewsdecoder``
package which uses Google's own batch API endpoint.

TRUSTED_DOMAINS is a whitelist of 15 high-quality Indian news outlets.
"""

import re
from datetime import datetime
from urllib.parse import quote_plus, urlparse

import feedparser
import httpx
from bs4 import BeautifulSoup
from googlenewsdecoder import gnewsdecoder
from loguru import logger

from backend.core.config import settings

# Only process articles from these domains.
TRUSTED_DOMAINS: set[str] = {
    "thehindu.com",
    "indianexpress.com",
    "ndtv.com",
    "hindustantimes.com",
    "thewire.in",
    "scroll.in",
    "theprint.in",
    "telegraphindia.com",
    "livemint.com",
    "businessstandard.com",
    "timesofindia.indiatimes.com",
    "deccanherald.com",
    "tribuneindia.com",
    "thequint.com",
    "newslaundry.com",
}

_HEADERS = {
    "User-Agent": settings.scraper_user_agent,
    "Accept-Language": "en-US,en;q=0.9",
}


# ─── URL / domain helpers ──────────────────────────────────────────────────────

def extract_domain(url: str | None) -> str:
    """Bare registrable host, leading ``www.`` stripped. Returns "" on garbage."""
    if not url:
        return ""
    try:
        host = urlparse(url).netloc.lower()
    except (ValueError, TypeError):
        return ""
    if host.startswith("www."):
        host = host[4:]
    return host


def entry_source_domain(entry) -> str:
    """Publisher domain for a Google News RSS entry.

    Prefers ``<source url=...>`` href (the real publisher hostname). Falls back
    to the ``entry.link`` domain, which for Google News RSS won't match the
    whitelist but avoids a KeyError.
    """
    source = getattr(entry, "source", None)
    if source is not None:
        href = source.get("href") if isinstance(source, dict) else getattr(source, "href", None)
        domain = extract_domain(href)
        if domain:
            return domain
    return extract_domain(getattr(entry, "link", None))


# ─── Google News RSS — discovery only ─────────────────────────────────────────

def fetch_rss(mp_name: str) -> list:
    """Query Google News RSS for an MP. Returns feedparser entries."""
    query = quote_plus(f'"{mp_name}" MP India')
    rss_url = (
        f"https://news.google.com/rss/search?q={query}"
        f"&hl=en-IN&gl=IN&ceid=IN:en"
    )
    feed = feedparser.parse(rss_url)
    if feed.bozo:
        logger.warning(f"RSS parse issue for {mp_name!r}: {feed.bozo_exception}")
    return feed.entries


def filter_by_whitelist(entries: list) -> list:
    """Keep only entries whose publishing outlet is on TRUSTED_DOMAINS."""
    return [e for e in entries if entry_source_domain(e) in TRUSTED_DOMAINS]


# ─── URL resolution ────────────────────────────────────────────────────────────

def resolve_article_url(gn_entry, mp_name: str) -> str | None:
    """Decode the encrypted Google News article URL to the real publisher URL.

    Google News RSS ``entry.link`` is a base64/protobuf encrypted redirect that
    can't be followed by a plain HTTP client. ``gnewsdecoder`` resolves it via
    Google's own batch API endpoint — no scraping, no JS execution required.
    """
    gn_url = getattr(gn_entry, "link", None)
    if not gn_url:
        return None
    try:
        result = gnewsdecoder(gn_url, interval=1)
        if result.get("status"):
            return result["decoded_url"]
        logger.debug(f"gnewsdecoder returned no URL for '{getattr(gn_entry, 'title', '')[:60]}'")
    except Exception as e:
        logger.warning(f"URL decode failed for '{getattr(gn_entry, 'title', '')[:60]}': {e}")
    return None


# ─── No-op cache hooks (kept for pipeline compatibility) ──────────────────────

def warm_feed_cache(domains=None) -> None:
    """No-op. Kept for backward compatibility with news_pipeline.py."""


def clear_feed_cache() -> None:
    """No-op. Kept for backward compatibility with news_pipeline.py."""


# ─── Date parsing ─────────────────────────────────────────────────────────────

def parse_date(published) -> datetime | None:
    """RSS ``published_parsed`` (time.struct_time) → naive UTC datetime."""
    if hasattr(published, "tm_year"):
        return datetime(*published[:6])
    return None


# ─── Article fetch + text extraction ─────────────────────────────────────────

def fetch_article(url: str) -> str | None:
    """Fetch the article HTML from a direct publisher URL."""
    try:
        with httpx.Client(
            timeout=20, headers=_HEADERS, follow_redirects=True
        ) as client:
            resp = client.get(url)
            resp.raise_for_status()
            ct = resp.headers.get("content-type", "")
            if "text/html" not in ct and "text/plain" not in ct:
                return None
            return resp.text
    except httpx.HTTPError as e:
        logger.warning(f"Article fetch failed for {url}: {e}")
        return None


def html_to_text(html: str) -> str:
    """Strip chrome/ads and return readable article body text.

    Prefers ``<p>`` paragraph content; falls back to full text dump.
    """
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(
        ["script", "style", "nav", "header", "footer", "aside",
         "form", "iframe", "noscript", "figure", "figcaption"]
    ):
        tag.decompose()

    paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    paragraphs = [p for p in paragraphs if len(p) > 40]

    if paragraphs:
        text = "\n".join(paragraphs)
    else:
        text = soup.get_text("\n", strip=True)
        text = "\n".join(line.strip() for line in text.splitlines() if line.strip())

    return re.sub(r"\n{3,}", "\n\n", text)[:8000]
