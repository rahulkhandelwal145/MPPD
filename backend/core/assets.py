"""Asset-growth helpers — how an MP's declared assets have changed over time.

`election_label` is free-text extracted by the LLM, so we pull a 4-digit year
out of it to order declarations chronologically. First-time MPs have no prior
declaration, so the growth helpers return None for them — the metric self-gates.

Two reference points are exposed:
  • `asset_growth`       — change since the most recent *prior* election.
  • `asset_growth_first` — change since the *earliest* declaration on record.
And `asset_series` returns the full chronological series for plotting.
"""

import re
from typing import Iterable, Optional

_YEAR_RE = re.compile(r"(?:19|20)\d{2}")

# The dataset is the 2024 (18th) Lok Sabha election. The extraction sometimes
# echoes the current declaration into asset_history, so we only treat strictly
# earlier elections as "prior".
CURRENT_ELECTION_YEAR = 2024

History = Iterable[tuple[Optional[str], Optional[int]]]


def parse_election_year(label: Optional[str]) -> Optional[int]:
    if not label:
        return None
    m = _YEAR_RE.search(label)
    return int(m.group(0)) if m else None


def _prior_declarations(history: History) -> list[tuple[int, str, int]]:
    """(year, label, assets) for every valid prior-election declaration, sorted
    oldest → newest. Entries without a parseable year, with a non-positive
    value, or at/after the current election are dropped."""
    out = []
    for label, assets in history:
        if assets is None or assets <= 0:
            continue
        year = parse_election_year(label)
        if year is None or year >= CURRENT_ELECTION_YEAR:
            continue
        out.append((year, label, assets))
    out.sort(key=lambda t: t[0])
    return out


def _growth(current_total: Optional[int], chosen) -> Optional[dict]:
    if current_total is None or chosen is None:
        return None
    _year, label, prev_assets = chosen
    return {
        "pct": round((current_total - prev_assets) / prev_assets * 100, 1),
        "since": label,
        "previous_assets": prev_assets,
    }


def previous_declaration(history: History):
    """(label, assets) for the most recent prior election, or None."""
    priors = _prior_declarations(history)
    if not priors:
        return None
    _year, label, assets = priors[-1]
    return label, assets


def asset_growth(current_total: Optional[int], history: History) -> Optional[dict]:
    """Percentage change since the most recent prior declaration."""
    priors = _prior_declarations(history)
    return _growth(current_total, priors[-1] if priors else None)


def asset_growth_first(current_total: Optional[int], history: History) -> Optional[dict]:
    """Percentage change since the earliest declaration on record (the MP's
    first contested election we have data for)."""
    priors = _prior_declarations(history)
    return _growth(current_total, priors[0] if priors else None)


def asset_series(current_total: Optional[int], history: History) -> list[dict]:
    """Chronological [{year, label, assets}] of prior declarations plus the
    current one — the points a sparkline / trajectory chart plots. Empty when
    there are no prior declarations (nothing to trend for a first-timer)."""
    priors = _prior_declarations(history)
    if not priors:
        return []
    points = [{"year": y, "label": l, "assets": a} for (y, l, a) in priors]
    if current_total is not None:
        points.append({
            "year": CURRENT_ELECTION_YEAR,
            "label": f"Lok Sabha {CURRENT_ELECTION_YEAR}",
            "assets": current_total,
        })
    return points
