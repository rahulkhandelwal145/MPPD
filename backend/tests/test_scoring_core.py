"""Tests for backend/core/scoring.py — compute_clean_record_score."""

import pytest
from backend.core.scoring import compute_clean_record_score


# ---------------------------------------------------------------------------
# Zero / defaults
# ---------------------------------------------------------------------------

def test_zero_convictions():
    assert compute_clean_record_score(0, 0) == 100


def test_default_arguments():
    assert compute_clean_record_score() == 100


def test_none_coerced_to_zero():
    assert compute_clean_record_score(None, None) == 100  # type: ignore[arg-type]


def test_negative_input_clamped_to_zero():
    assert compute_clean_record_score(-5, -3) == 100


# ---------------------------------------------------------------------------
# Serious convictions only  (-50 for first 3, -25 from 4th)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("serious, expected", [
    (0, 100),
    (1,  50),   # 100 - 50
    (2,   0),   # 100 - 50 - 50 = 0
    (3,   0),   # 100 - 50*3 = -50 → floor 0
    (4,   0),   # 4th uses -25, but already at 0
    (5,   0),
])
def test_serious_only(serious, expected):
    assert compute_clean_record_score(convictions_serious=serious) == expected


# ---------------------------------------------------------------------------
# Minor convictions only  (-20 for first 3, -10 from 4th)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("minor, expected", [
    (0, 100),
    (1,  80),   # 100 - 20
    (2,  60),   # 100 - 40
    (3,  40),   # 100 - 60
    (4,  30),   # 100 - 60 - 10  (4th switches to -10)
    (5,  20),
    (6,  10),
    (7,   0),
    (8,   0),   # floor holds
])
def test_minor_only(minor, expected):
    assert compute_clean_record_score(convictions_minor=minor) == expected


def test_minor_penalty_switches_at_fourth():
    """Verify the -20 → -10 switch at index 3 (4th conviction)."""
    assert compute_clean_record_score(convictions_minor=3) == 40   # 3 × -20
    assert compute_clean_record_score(convictions_minor=4) == 30   # 3 × -20 + 1 × -10


# ---------------------------------------------------------------------------
# Mixed serious + minor
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("serious, minor, expected", [
    (1, 1, 30),   # 100 - 50 - 20
    (1, 3,  0),   # 100 - 50 - 60 = -10 → 0
    (2, 2,  0),   # 100 - 100 - 40 → 0
    (0, 5, 20),   # 100 - 60 - 20 = 20
])
def test_mixed(serious, minor, expected):
    assert compute_clean_record_score(serious, minor) == expected


def test_many_convictions_floor():
    assert compute_clean_record_score(10, 20) == 0


# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------

def test_returns_int():
    assert isinstance(compute_clean_record_score(1, 2), int)


def test_floor_returns_int_zero():
    result = compute_clean_record_score(10, 10)
    assert result == 0
    assert isinstance(result, int)
