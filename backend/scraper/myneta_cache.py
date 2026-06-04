from pathlib import Path

CACHE_DIR = Path("./data/cache/myneta")


def get(key: str) -> str | None:
    path = CACHE_DIR / f"{key}.html"
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def set(key: str, html: str) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{key}.html"
    path.write_text(html, encoding="utf-8")
