from pathlib import Path
from backend.core.config import settings

CACHE_DIR = Path(settings.scraper_cache_dir)


def get(slug: str) -> str | None:
    path = CACHE_DIR / f"{slug}.html"
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def set(slug: str, html: str) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{slug}.html"
    path.write_text(html, encoding="utf-8")
