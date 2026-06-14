"""Tests for the pure logic in backend/api/routes/mps.py.

Tests _summary_from_row and _summary_from_row-derived computed fields
(clean_record_score, total_score, asset_growth_pct) without requiring a live
database or FastAPI TestClient.
"""

import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock

from backend.api.routes.mps import _summary_from_row


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _profile(**kwargs):
    defaults = dict(
        id=1, name="Test MP", prs_slug="test-mp",
        constituency="Pune", state="Maharashtra", party="INC",
        is_minister=False, is_speaker=False, is_loa=False,
        age=50, gender="M", education="Graduate", terms=2,
        image_url=None,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _score(**kwargs):
    defaults = dict(
        attendance_score=75.0, questions_score=60.0,
        debates_score=55.0, pmb_score=50.0,
        peer_group="non-minister", total_peers=490,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _row(profile=None, score=None, criminal_cases=0, convictions=0,
         convictions_serious=0, total_assets=None, serious=None,
         mplads_score=None, mplads_util=None, flagged_count=None):
    return (
        profile or _profile(),
        score or _score(),
        criminal_cases, convictions, convictions_serious,
        total_assets, serious, mplads_score, mplads_util, flagged_count,
    )


# ---------------------------------------------------------------------------
# clean_record_score derivation
# ---------------------------------------------------------------------------

def test_clean_record_score_none_when_no_affidavit():
    summary = _summary_from_row(_row(convictions=None, convictions_serious=None))
    assert summary.clean_record_score is None


def test_clean_record_score_100_when_no_convictions():
    summary = _summary_from_row(_row(convictions=0, convictions_serious=0))
    assert summary.clean_record_score == 100


def test_clean_record_score_reduced_for_serious_conviction():
    summary = _summary_from_row(_row(convictions=1, convictions_serious=1))
    assert summary.clean_record_score == 50  # 100 - 50


def test_clean_record_score_minor_conviction():
    # 1 total conviction, 0 serious → 1 minor
    summary = _summary_from_row(_row(convictions=1, convictions_serious=0))
    assert summary.clean_record_score == 80  # 100 - 20


def test_clean_record_score_floored_at_zero():
    summary = _summary_from_row(_row(convictions=5, convictions_serious=5))
    assert summary.clean_record_score == 0


def test_clean_record_score_mixed():
    # 2 convictions, 1 serious → 1 serious (-50) + 1 minor (-20) = 30
    summary = _summary_from_row(_row(convictions=2, convictions_serious=1))
    assert summary.clean_record_score == 30


# ---------------------------------------------------------------------------
# total_score computation
# ---------------------------------------------------------------------------

def test_total_score_mean_of_available_metrics():
    score = _score(attendance_score=80.0, questions_score=60.0, debates_score=None, pmb_score=None)
    # clean_record_score: convictions=0, serious=0 → 100
    summary = _summary_from_row(_row(score=score, convictions=0, convictions_serious=0))
    # mean(80, 60, 100) = 80.0
    assert summary.total_score == pytest.approx(80.0, abs=0.1)


def test_total_score_none_when_all_metrics_none():
    score = _score(attendance_score=None, questions_score=None, debates_score=None, pmb_score=None)
    summary = _summary_from_row(_row(score=score, convictions=None))
    assert summary.total_score is None


def test_total_score_includes_clean_record():
    score = _score(attendance_score=100.0, questions_score=None, debates_score=None, pmb_score=None)
    summary = _summary_from_row(_row(score=score, convictions=0, convictions_serious=0))
    # mean(100, 100) = 100
    assert summary.total_score == pytest.approx(100.0)


def test_total_score_excludes_clean_record_when_no_affidavit():
    score = _score(attendance_score=80.0, questions_score=None, debates_score=None, pmb_score=None)
    summary = _summary_from_row(_row(score=score, convictions=None))
    # Only attendance: mean(80.0) = 80.0
    assert summary.total_score == pytest.approx(80.0)


# ---------------------------------------------------------------------------
# Asset growth gating on terms
# ---------------------------------------------------------------------------

def test_asset_growth_shown_for_returning_mp():
    profile = _profile(terms=2)
    growth_map = {1: {"pct": 100.0, "since": "Election 2019", "first_pct": 200.0, "first_since": "Election 2014", "series": []}}
    summary = _summary_from_row(_row(profile=profile), growth_map=growth_map)
    assert summary.asset_growth_pct == 100.0
    assert summary.asset_growth_since == "Election 2019"


def test_asset_growth_hidden_for_first_time_mp():
    """terms=1 means no prior Lok Sabha declaration — growth suppressed."""
    profile = _profile(terms=1)
    growth_map = {1: {"pct": 500.0, "since": "Election 2019", "first_pct": None, "first_since": None, "series": []}}
    summary = _summary_from_row(_row(profile=profile), growth_map=growth_map)
    assert summary.asset_growth_pct is None


def test_asset_growth_none_when_not_in_growth_map():
    profile = _profile(terms=3)
    summary = _summary_from_row(_row(profile=profile), growth_map={})
    assert summary.asset_growth_pct is None


# ---------------------------------------------------------------------------
# Basic field passthrough
# ---------------------------------------------------------------------------

def test_name_passed_through():
    profile = _profile(name="Narendra Modi", prs_slug="narendra-modi")
    summary = _summary_from_row(_row(profile=profile))
    assert summary.name == "Narendra Modi"
    assert summary.prs_slug == "narendra-modi"


def test_criminal_cases_passed_through():
    summary = _summary_from_row(_row(criminal_cases=3))
    assert summary.criminal_cases == 3


def test_total_assets_passed_through():
    summary = _summary_from_row(_row(total_assets=50_000_000))
    assert summary.total_assets == 50_000_000


def test_flagged_count_passed_through():
    summary = _summary_from_row(_row(flagged_count=5))
    assert summary.flagged_count == 5


def test_has_serious_cases_true():
    summary = _summary_from_row(_row(serious=1))
    assert summary.has_serious_cases is True


def test_has_serious_cases_false():
    summary = _summary_from_row(_row(serious=0))
    assert summary.has_serious_cases is False


def test_has_serious_cases_none_when_no_affidavit():
    summary = _summary_from_row(_row(serious=None))
    assert summary.has_serious_cases is None


def test_minister_flag_passed_through():
    profile = _profile(is_minister=True)
    score = _score(questions_score=None, debates_score=None, pmb_score=None, peer_group="minister")
    summary = _summary_from_row(_row(profile=profile, score=score))
    assert summary.is_minister is True


def test_mplads_score_passed_through():
    # mplads_score is typed as int in MPSummary; use int values
    summary = _summary_from_row(_row(mplads_score=82, mplads_util=75.0))
    assert summary.mplads_score == 82
    assert summary.mplads_utilization_pct == 75.0
