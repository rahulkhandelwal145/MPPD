import re
import time

import httpx
from bs4 import BeautifulSoup
from loguru import logger
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from backend.core.config import settings
from backend.scraper import myneta_cache as cache

WINNERS_URL = (
    "https://myneta.info/LokSabha2024/index.php"
    "?action=show_winners&sort=default"
)
CANDIDATE_URL = "https://myneta.info/LokSabha2024/candidate.php?candidate_id={id}"
SEARCH_URL = "https://myneta.info/search_myneta.php"

_LS2024_CID_RE = re.compile(r"LokSabha2024[^\"']*candidate_id=(\d+)")


def search_ls2024_candidates(name: str) -> list[tuple[int, str]]:
    """Search MyNeta globally and return (candidate_id, displayed_name) for the
    LokSabha2024 results — used to find winners absent from the winners index."""
    resp = fetch_page(f"{SEARCH_URL}?q={name.replace(' ', '+')}")
    soup = BeautifulSoup(resp, "lxml")
    out: list[tuple[int, str]] = []
    seen: set[int] = set()
    for a in soup.find_all("a", href=_LS2024_CID_RE):
        cid = int(_LS2024_CID_RE.search(a["href"]).group(1))
        if cid in seen:
            continue
        seen.add(cid)
        out.append((cid, a.get_text(strip=True)))
    return out

_HEADERS = {"User-Agent": settings.scraper_user_agent}
_CANDIDATE_ID_RE = re.compile(r"candidate_id=(\d+)")


@retry(
    retry=retry_if_exception_type(httpx.HTTPError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
)
def fetch_page(url: str) -> str:
    with httpx.Client(timeout=10, headers=_HEADERS) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.text


def fetch_with_cache(url: str, cache_key: str, force: bool = False) -> str:
    if not force:
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
    html = fetch_page(url)
    cache.set(cache_key, html)
    return html


def parse_winners_index(html: str) -> list[dict]:
    """Parse the winners index page; returns list of dicts with candidate data.

    Table columns: S.No | Name | Constituency | Party | Criminal | Education | Assets | Liabilities
    Each row has two candidate links — an icon link (empty text) and a named link.
    """
    soup = BeautifulSoup(html, "lxml")
    candidates = []
    seen_ids: set[int] = set()

    for row in soup.find_all("tr"):
        # Pick the link that actually has text (skip the icon/image link)
        named_link = None
        for link in row.find_all("a", href=_CANDIDATE_ID_RE):
            if link.get_text(strip=True):
                named_link = link
                break

        if named_link is None:
            continue

        href = named_link.get("href", "")
        match = _CANDIDATE_ID_RE.search(href)
        if not match:
            continue

        candidate_id = int(match.group(1))
        if candidate_id in seen_ids:
            continue
        seen_ids.add(candidate_id)

        candidate_name = named_link.get_text(strip=True)
        cells = row.find_all("td")
        cell_texts = [c.get_text(strip=True) for c in cells]

        # S.No=0 | Name=1 | Constituency=2 | Party=3 | Criminal=4 | Education=5 | ...
        constituency = cell_texts[2] if len(cell_texts) > 2 else ""
        party = cell_texts[3] if len(cell_texts) > 3 else ""

        candidates.append({
            "candidate_id": candidate_id,
            "name": candidate_name,
            "constituency": constituency,
            "state": "",  # not present in table
            "party": party,
        })

    return candidates


# IPC/section codes considered "serious" (mirrors extraction_agent.SERIOUS_SECTIONS).
SERIOUS_SECTIONS = {
    "302", "307", "376", "354", "364", "395", "396", "397",
    "120B", "124A", "153A", "295A", "420", "467", "468", "471",
}
_SECTION_TOKEN_RE = re.compile(r"\d+[A-Za-z]?")


def _conviction_ipc_rows(html: str) -> list[str]:
    """Return the IPC-sections text for each real row in the 'Cases where
    Convicted' table (excludes the header and the '----No Cases----' placeholder)."""
    soup = BeautifulSoup(html, "lxml")
    heading = next(
        (h for h in soup.find_all("h3") if "Cases where Convicted" in h.get_text()),
        None,
    )
    if heading is None:
        return []
    panel = heading.find_parent("div")
    table = panel.find_next("table") if panel else None
    if table is None:
        return []

    rows: list[str] = []
    for tr in table.find_all("tr"):
        cells = tr.find_all("td")
        if not cells:
            continue
        if re.fullmatch(r"\d+", cells[0].get_text(strip=True)):
            # 4th column is "IPC Sections Applicable"; fall back to "" if absent.
            rows.append(cells[3].get_text(" ", strip=True) if len(cells) > 3 else "")
    return rows


def _is_serious_ipc(ipc_text: str) -> bool:
    return any(tok.upper() in SERIOUS_SECTIONS for tok in _SECTION_TOKEN_RE.findall(ipc_text))


def count_convictions(html: str) -> int:
    """Total real rows in MyNeta's 'Cases where Convicted' table."""
    return len(_conviction_ipc_rows(html))


def count_serious_convictions(html: str) -> int:
    """Of the convictions, how many cite a serious IPC section."""
    return sum(1 for ipc in _conviction_ipc_rows(html) if _is_serious_ipc(ipc))


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "nav", "header",
                     "footer", "img", "a", "iframe",
                     "noscript", "meta", "link"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)[:6000]
