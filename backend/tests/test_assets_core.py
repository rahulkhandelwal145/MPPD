"""Tests for backend/core/assets.py — asset_growth, asset_growth_first, asset_series."""

import pytest
from backend.core.assets import (
    CURRENT_ELECTION_YEAR,
    asset_growth,
    asset_growth_first,
    asset_series,
    parse_election_year,
    previous_declaration,
)


# ---------------------------------------------------------------------------
# parse_election_year
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("label, expected", [
    ("General Election 2019", 2019),
    ("Lok Sabha 2014", 2014),
    ("2009 Election", 2009),
    ("18th Lok Sabha 2024", 2024),
    ("No year here", None),
    ("", None),
    (None, None),
    ("Year: 20xx", None),
    ("Election 1899", None),  # 18xx doesn't match (?:19|20)
])
def test_parse_election_year(label, expected):
    assert parse_election_year(label) == expected


def test_parse_election_year_returns_int():
    assert isinstance(parse_election_year("Election 2019"), int)


def test_parse_election_year_picks_first_match():
    assert parse_election_year("2014 re-run in 2019") == 2014


# ---------------------------------------------------------------------------
# previous_declaration
# ---------------------------------------------------------------------------

def test_previous_declaration_returns_most_recent():
    history = [("Election 2014", 1_000_000), ("Election 2019", 2_000_000)]
    label, assets = previous_declaration(history)
    assert label == "Election 2019"
    assert assets == 2_000_000


def test_previous_declaration_none_when_empty():
    assert previous_declaration([]) is None


def test_previous_declaration_none_when_only_current_year():
    history = [(f"Lok Sabha {CURRENT_ELECTION_YEAR}", 5_000_000)]
    assert previous_declaration(history) is None


def test_previous_declaration_none_when_zero_assets():
    assert previous_declaration([("Election 2019", 0)]) is None


# ---------------------------------------------------------------------------
# asset_growth — % change since most recent prior declaration
# ---------------------------------------------------------------------------

def test_asset_growth_single_prior():
    result = asset_growth(2_000_000, [("Election 2019", 1_000_000)])
    assert result is not None
    assert result["pct"] == 100.0
    assert result["since"] == "Election 2019"
    assert result["previous_assets"] == 1_000_000


def test_asset_growth_uses_most_recent_prior():
    history = [("Election 2014", 500_000), ("Election 2019", 1_000_000)]
    result = asset_growth(3_000_000, history)
    assert result["since"] == "Election 2019"
    assert result["pct"] == 200.0


def test_asset_growth_ignores_current_election_year_entry():
    history = [("Election 2019", 1_000_000), (f"Lok Sabha {CURRENT_ELECTION_YEAR}", 9_000_000)]
    result = asset_growth(2_000_000, history)
    assert result["since"] == "Election 2019"
    assert result["pct"] == 100.0


def test_asset_growth_none_when_no_history():
    assert asset_growth(1_000_000, []) is None


def test_asset_growth_none_when_current_total_none():
    assert asset_growth(None, [("Election 2019", 1_000_000)]) is None


def test_asset_growth_negative_growth():
    result = asset_growth(1_000_000, [("Election 2019", 2_000_000)])
    assert result["pct"] == -50.0


def test_asset_growth_rounding():
    result = asset_growth(4_000_000, [("Election 2019", 3_000_000)])
    assert result["pct"] == 33.3  # 33.333... → 33.3


def test_asset_growth_zero_asset_entry_skipped():
    history = [("Election 2019", 0), ("Election 2014", 500_000)]
    result = asset_growth(1_000_000, history)
    assert result["since"] == "Election 2014"
    assert result["pct"] == 100.0


def test_asset_growth_unsorted_history_uses_most_recent():
    history = [("Election 2019", 2_000_000), ("Election 2009", 500_000), ("Election 2014", 1_000_000)]
    result = asset_growth(4_000_000, history)
    assert result["since"] == "Election 2019"


def test_asset_growth_unparseable_label_skipped():
    history = [("Unknown election", 1_000_000), ("Election 2014", 500_000)]
    result = asset_growth(1_500_000, history)
    assert result["since"] == "Election 2014"


# ---------------------------------------------------------------------------
# asset_growth_first — % change since earliest declaration
# ---------------------------------------------------------------------------

def test_asset_growth_first_single_prior():
    result = asset_growth_first(2_000_000, [("Election 2014", 500_000)])
    assert result["pct"] == 300.0
    assert result["since"] == "Election 2014"


def test_asset_growth_first_uses_earliest():
    history = [("Election 2019", 2_000_000), ("Election 2009", 200_000)]
    result = asset_growth_first(4_000_000, history)
    assert result["since"] == "Election 2009"
    assert result["pct"] == 1900.0


def test_asset_growth_first_differs_from_recent():
    history = [("Election 2014", 500_000), ("Election 2019", 1_000_000)]
    recent = asset_growth(3_000_000, history)
    first = asset_growth_first(3_000_000, history)
    assert recent["previous_assets"] == 1_000_000
    assert first["previous_assets"] == 500_000


def test_asset_growth_first_none_when_no_history():
    assert asset_growth_first(1_000_000, []) is None


def test_asset_growth_first_negative_growth():
    history = [("Election 2009", 5_000_000), ("Election 2014", 4_000_000)]
    result = asset_growth_first(3_000_000, history)
    assert result["pct"] == -40.0


# ---------------------------------------------------------------------------
# asset_series — chronological list for sparklines
# ---------------------------------------------------------------------------

def test_asset_series_empty_when_no_history():
    assert asset_series(2_000_000, []) == []


def test_asset_series_single_prior_plus_current():
    series = asset_series(2_000_000, [("Election 2019", 1_000_000)])
    assert len(series) == 2
    assert series[0] == {"year": 2019, "label": "Election 2019", "assets": 1_000_000}
    assert series[1] == {"year": CURRENT_ELECTION_YEAR, "label": f"Lok Sabha {CURRENT_ELECTION_YEAR}", "assets": 2_000_000}


def test_asset_series_sorted_chronologically():
    history = [("Election 2019", 2_000_000), ("Election 2009", 300_000), ("Election 2014", 800_000)]
    series = asset_series(5_000_000, history)
    years = [p["year"] for p in series]
    assert years == sorted(years)
    assert years[0] == 2009
    assert years[-1] == CURRENT_ELECTION_YEAR


def test_asset_series_excludes_history_entry_at_current_year():
    history = [(f"Lok Sabha {CURRENT_ELECTION_YEAR}", 3_000_000), ("Election 2019", 1_000_000)]
    series = asset_series(4_000_000, history)
    assert len(series) == 2
    assert series[0]["year"] == 2019
    assert series[1]["year"] == CURRENT_ELECTION_YEAR
    assert series[1]["assets"] == 4_000_000


def test_asset_series_no_current_total_omits_current_point():
    history = [("Election 2014", 500_000), ("Election 2019", 1_000_000)]
    series = asset_series(None, history)
    assert len(series) == 2
    assert all(p["year"] < CURRENT_ELECTION_YEAR for p in series)


def test_asset_series_skips_zero_asset_entries():
    history = [("Election 2019", 0), ("Election 2014", None), ("Election 2009", 200_000)]
    series = asset_series(1_000_000, history)
    assert len(series) == 2
    assert series[0]["year"] == 2009
    assert series[1]["year"] == CURRENT_ELECTION_YEAR


def test_asset_series_structure():
    series = asset_series(3_000_000, [("Election 2019", 1_500_000)])
    for point in series:
        assert "year" in point
        assert "label" in point
        assert "assets" in point
        assert isinstance(point["year"], int)


def test_asset_series_returns_empty_when_all_history_at_current_year():
    history = [(f"Lok Sabha {CURRENT_ELECTION_YEAR}", 5_000_000)]
    assert asset_series(5_000_000, history) == []


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

def test_current_election_year():
    assert CURRENT_ELECTION_YEAR == 2024


# ---------------------------------------------------------------------------
# Integration: growth + series agree
# ---------------------------------------------------------------------------

def test_growth_and_series_agree():
    history = [("Election 2009", 200_000), ("Election 2014", 600_000), ("Election 2019", 1_500_000)]
    current = 4_000_000
    series = asset_series(current, history)
    recent = asset_growth(current, history)
    first = asset_growth_first(current, history)

    assert len(series) == 4
    assert recent["previous_assets"] == series[-2]["assets"]
    assert first["previous_assets"] == series[0]["assets"]
