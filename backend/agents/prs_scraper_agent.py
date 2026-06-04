from pathlib import Path
from urllib.parse import quote

import httpx
from loguru import logger

from backend.core.config import settings
from backend.scraper.prs import parse_csv_download, parse_image_url

DOWNLOAD_URL = (
    "https://prsindia.org/mptrack/download"
    "?file_path=" + quote("files/mptrack/18-lok-sabha/Mp-Track/18 LS MP Track.csv")
)
_CACHE_PATH = Path(settings.scraper_cache_dir) / "prs_18ls_download.csv"


async def run_prs_scraper(run_id: int, force_refresh: bool = False) -> dict:
    csv_bytes: bytes | None = None

    if not force_refresh and _CACHE_PATH.exists():
        logger.info("Using cached PRS download from {}", _CACHE_PATH)
        csv_bytes = _CACHE_PATH.read_bytes()

    if csv_bytes is None:
        logger.info("Downloading 18th LS MP data from {}", DOWNLOAD_URL)
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                DOWNLOAD_URL,
                headers={"User-Agent": settings.scraper_user_agent},
                follow_redirects=True,
            )
            response.raise_for_status()
            csv_bytes = response.content
        _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _CACHE_PATH.write_bytes(csv_bytes)
        logger.info("Cached PRS download ({} bytes) to {}", len(csv_bytes), _CACHE_PATH)

    raw_mp_data = parse_csv_download(csv_bytes)
    slugs = [row["slug"] for row in raw_mp_data]
    logger.info("Parsed {} MP records from PRS download", len(raw_mp_data))

    html_cache_dir = Path(settings.scraper_cache_dir)
    images_found = 0
    for row in raw_mp_data:
        html_path = html_cache_dir / f"{row['slug']}.html"
        if html_path.exists():
            row["image_url"] = parse_image_url(html_path.read_bytes())
            if row["image_url"]:
                images_found += 1
        else:
            row["image_url"] = None
    logger.info("Extracted image URLs for {}/{} MPs from HTML cache", images_found, len(raw_mp_data))

    return {
        "mp_slugs": slugs,
        "raw_mp_data": raw_mp_data,
        "errors": [],
    }
