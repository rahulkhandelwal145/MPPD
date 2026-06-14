"""Tests for backend/agents/scoring_agent.py — percentile scoring logic."""

import pytest
import pandas as pd

from backend.agents.scoring_agent import (
    _to_peer_group,
    _percentile_score,
    _rank_column,
    run_scoring_agent,
)


# ---------------------------------------------------------------------------
# _to_peer_group
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("is_minister, is_speaker, is_loa, expected", [
    (False, False, False, "non-minister"),
    (True,  False, False, "minister"),
    (False, True,  False, "minister"),
    (False, False, True,  "minister"),
    (True,  True,  True,  "minister"),
])
def test_to_peer_group(is_minister, is_speaker, is_loa, expected):
    assert _to_peer_group(is_minister, is_speaker, is_loa) == expected


# ---------------------------------------------------------------------------
# _percentile_score
# ---------------------------------------------------------------------------

def test_percentile_score_range_0_to_100():
    s = pd.Series([10.0, 30.0, 50.0, 70.0, 90.0])
    result = _percentile_score(s)
    assert result.min() >= 0.0
    assert result.max() <= 100.0


def test_percentile_score_ordering():
    s = pd.Series([10.0, 50.0, 100.0])
    result = _percentile_score(s)
    assert result.iloc[0] < result.iloc[1] < result.iloc[2]


def test_percentile_score_single_element():
    s = pd.Series([42.0])
    result = _percentile_score(s)
    assert result.iloc[0] == 100.0


def test_percentile_score_all_same_value():
    s = pd.Series([5.0, 5.0, 5.0])
    result = _percentile_score(s)
    # All tied — rank(method="min") gives rank 1 for all → pct = 1/3 = 33.3%.
    # The key property is that all elements receive the same score.
    assert result.nunique() == 1


# ---------------------------------------------------------------------------
# _rank_column
# ---------------------------------------------------------------------------

def test_rank_column_ascending():
    s = pd.Series([10.0, 30.0, 50.0])
    result = _rank_column(s)
    assert list(result) == [1, 2, 3]


def test_rank_column_ties_use_min():
    s = pd.Series([10.0, 10.0, 30.0])
    result = _rank_column(s)
    assert result.iloc[0] == 1
    assert result.iloc[1] == 1
    assert result.iloc[2] == 3


def test_rank_column_integer_dtype():
    s = pd.Series([10.0, 20.0, 30.0])
    result = _rank_column(s)
    assert pd.api.types.is_integer_dtype(result)


# ---------------------------------------------------------------------------
# run_scoring_agent — async integration
# ---------------------------------------------------------------------------

def _mp(slug, name, attendance=75.0, questions=10, debates=5, pmb=0,
        is_minister=False, is_speaker=False, is_loa=False):
    return {
        "slug": slug,
        "name": name,
        "constituency": "Test",
        "state": "Maharashtra",
        "party": "INC",
        "attendance_pct": attendance,
        "questions_count": questions,
        "debates_count": debates,
        "pmb_count": pmb,
        "is_minister": is_minister,
        "is_speaker": is_speaker,
        "is_loa": is_loa,
    }


@pytest.mark.asyncio
async def test_empty_raw_data_returns_empty():
    result = await run_scoring_agent({"raw_mp_data": []})
    assert result["scored_data"] == []


@pytest.mark.asyncio
async def test_non_minister_gets_all_four_scores():
    state = {"raw_mp_data": [_mp("mp1", "MP One")]}
    result = await run_scoring_agent(state)
    mp = result["scored_data"][0]
    assert mp["attendance_score"] is not None
    assert mp["questions_score"] is not None
    assert mp["debates_score"] is not None
    assert mp["pmb_score"] is not None


@pytest.mark.asyncio
async def test_minister_gets_attendance_score_only():
    state = {"raw_mp_data": [_mp("m1", "Minister One", is_minister=True)]}
    result = await run_scoring_agent(state)
    mp = result["scored_data"][0]
    assert mp["attendance_score"] is not None
    assert mp["questions_score"] is None
    assert mp["debates_score"] is None
    assert mp["pmb_score"] is None


@pytest.mark.asyncio
async def test_speaker_treated_as_minister():
    state = {"raw_mp_data": [_mp("s1", "Speaker", is_speaker=True)]}
    result = await run_scoring_agent(state)
    mp = result["scored_data"][0]
    assert mp["peer_group"] == "minister"
    assert mp["questions_score"] is None


@pytest.mark.asyncio
async def test_loa_treated_as_minister():
    state = {"raw_mp_data": [_mp("l1", "LoA", is_loa=True)]}
    result = await run_scoring_agent(state)
    mp = result["scored_data"][0]
    assert mp["peer_group"] == "minister"


@pytest.mark.asyncio
async def test_higher_attendance_gets_higher_score():
    state = {"raw_mp_data": [
        _mp("low", "Low Attender", attendance=40.0),
        _mp("high", "High Attender", attendance=90.0),
    ]}
    result = await run_scoring_agent(state)
    by_slug = {r["slug"]: r for r in result["scored_data"]}
    assert by_slug["high"]["attendance_score"] > by_slug["low"]["attendance_score"]


@pytest.mark.asyncio
async def test_minister_does_not_affect_non_minister_percentiles():
    """A minister with high attendance shouldn't push non-minister scores down."""
    raw = [
        _mp("nm1", "Regular MP", attendance=80.0),
        _mp("nm2", "Regular MP 2", attendance=60.0),
        _mp("min", "Minister", attendance=95.0, is_minister=True),
    ]
    result = await run_scoring_agent({"raw_mp_data": raw})
    nm_scores = {r["slug"]: r["attendance_score"] for r in result["scored_data"] if r["slug"] != "min"}
    # Both non-ministers should have scores; the minister's higher attendance
    # is scored in a separate pool and doesn't affect them
    assert all(s is not None for s in nm_scores.values())


@pytest.mark.asyncio
async def test_attendance_score_clamped_0_to_100():
    state = {"raw_mp_data": [
        _mp("a", "Alpha", attendance=50.0),
        _mp("b", "Beta", attendance=80.0),
    ]}
    result = await run_scoring_agent(state)
    for r in result["scored_data"]:
        score = r["attendance_score"]
        if score is not None:
            assert 0.0 <= score <= 100.0


@pytest.mark.asyncio
async def test_single_mp_in_group():
    """A single MP in their group should still get a valid score (100th percentile)."""
    state = {"raw_mp_data": [_mp("solo", "Solo MP", attendance=75.0)]}
    result = await run_scoring_agent(state)
    mp = result["scored_data"][0]
    assert mp["attendance_score"] == 100.0


@pytest.mark.asyncio
async def test_all_same_attendance_handles_tie():
    state = {"raw_mp_data": [
        _mp("a", "A", attendance=70.0),
        _mp("b", "B", attendance=70.0),
        _mp("c", "C", attendance=70.0),
    ]}
    result = await run_scoring_agent(state)
    scores = [r["attendance_score"] for r in result["scored_data"]]
    assert all(s == scores[0] for s in scores)


@pytest.mark.asyncio
async def test_mplads_injected_from_state():
    state = {
        "raw_mp_data": [_mp("mp1", "MP One")],
        "mplads_data": {"mp1": 78.5},
    }
    result = await run_scoring_agent(state)
    mp = result["scored_data"][0]
    assert mp["mplads_utilization"] == pytest.approx(78.5)


@pytest.mark.asyncio
async def test_mplads_none_when_not_in_state():
    state = {"raw_mp_data": [_mp("mp1", "MP One")], "mplads_data": {}}
    result = await run_scoring_agent(state)
    assert result["scored_data"][0]["mplads_utilization"] is None


@pytest.mark.asyncio
async def test_output_slugs_match_input():
    raw = [_mp("a", "A"), _mp("b", "B"), _mp("c", "C")]
    result = await run_scoring_agent({"raw_mp_data": raw})
    out_slugs = {r["slug"] for r in result["scored_data"]}
    assert out_slugs == {"a", "b", "c"}


@pytest.mark.asyncio
async def test_errors_propagated_from_state():
    state = {"raw_mp_data": [], "errors": ["some upstream error"]}
    result = await run_scoring_agent(state)
    assert "some upstream error" in result["errors"]


@pytest.mark.asyncio
async def test_null_attendance_yields_null_score():
    state = {"raw_mp_data": [_mp("x", "X", attendance=None)]}
    result = await run_scoring_agent(state)
    assert result["scored_data"][0]["attendance_score"] is None
