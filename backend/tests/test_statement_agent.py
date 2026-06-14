"""Tests for backend/agents/statement_agent.py — classification guard logic."""

import json
import time
from unittest.mock import MagicMock, patch

import pytest
from groq import RateLimitError

from backend.agents.statement_agent import (
    VALID_CATEGORIES,
    _DATA_REQUIRED,
    _sleep_for_rate_limit,
    _strip_fences,
    classify_statement,
    extract_quotes,
)


# ---------------------------------------------------------------------------
# _strip_fences
# ---------------------------------------------------------------------------

def test_strip_fences_removes_json_fence():
    raw = "```json\n{\"key\": \"val\"}\n```"
    assert _strip_fences(raw) == '{"key": "val"}'


def test_strip_fences_removes_plain_fence():
    raw = "```\n{\"key\": \"val\"}\n```"
    assert _strip_fences(raw) == '{"key": "val"}'


def test_strip_fences_no_fence_unchanged():
    raw = '{"key": "val"}'
    assert _strip_fences(raw) == raw


def test_strip_fences_empty_string():
    assert _strip_fences("") == ""


# ---------------------------------------------------------------------------
# _sleep_for_rate_limit
# ---------------------------------------------------------------------------

def _make_rate_limit_error(msg: str) -> RateLimitError:
    err = MagicMock(spec=RateLimitError)
    err.__str__ = lambda self: msg
    return err


@patch("backend.agents.statement_agent.time.sleep")
def test_sleep_parses_seconds(mock_sleep):
    err = _make_rate_limit_error("try again in 30s")
    _sleep_for_rate_limit(err)
    mock_sleep.assert_called_once()
    waited = mock_sleep.call_args[0][0]
    assert waited == pytest.approx(35.0)  # 30 + 5 buffer


@patch("backend.agents.statement_agent.time.sleep")
def test_sleep_parses_minutes_and_seconds(mock_sleep):
    err = _make_rate_limit_error("try again in 1m30s")
    _sleep_for_rate_limit(err)
    waited = mock_sleep.call_args[0][0]
    assert waited == pytest.approx(95.0)  # 60 + 30 + 5


@patch("backend.agents.statement_agent.time.sleep")
def test_sleep_defaults_to_65_when_no_match(mock_sleep):
    err = _make_rate_limit_error("rate limit exceeded, please wait")
    _sleep_for_rate_limit(err)
    mock_sleep.assert_called_once_with(65)


# ---------------------------------------------------------------------------
# Helpers for classify_statement tests
# ---------------------------------------------------------------------------

def _classify(llm_response: dict, **kwargs) -> dict | None:
    """Call classify_statement with a mocked LLM response."""
    defaults = dict(
        statement="Test statement text",
        context="Some context",
        mp_name="Test MP",
        source="thehindu.com",
        date="2024-06-01",
    )
    defaults.update(kwargs)
    raw = json.dumps(llm_response)
    with patch("backend.agents.statement_agent._call_llm", return_value=raw):
        return classify_statement(**defaults)


# ---------------------------------------------------------------------------
# Guard 1: confidence < 70 → force E
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("confidence", [0, 50, 69])
def test_low_confidence_forced_to_E(confidence):
    result = _classify({"category": "A1", "speaker_is_mp": True, "confidence": confidence,
                         "data_contradicted": None, "constitutional_anchor": None, "reason": ""})
    assert result["category"] == "E"


def test_confidence_70_not_forced_to_E():
    result = _classify({"category": "D1", "speaker_is_mp": True, "confidence": 70, "reason": ""})
    assert result["category"] == "D1"


def test_confidence_100_not_forced_to_E():
    result = _classify({"category": "A3", "speaker_is_mp": True, "confidence": 100,
                         "data_contradicted": None, "constitutional_anchor": "Article 14", "reason": ""})
    assert result["category"] == "A3"


# ---------------------------------------------------------------------------
# Guard 2: speaker_is_mp=false + A/B/C → force E
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("category", [
    "A1", "A2", "A3", "A4", "A5",
    "B1", "B2", "B3", "B4", "B5",
    "C1", "C2", "C3",
])
def test_not_speaker_abc_forced_to_E(category):
    result = _classify({
        "category": category,
        "speaker_is_mp": False,
        "confidence": 90,
        "data_contradicted": "CMIE data",
        "constitutional_anchor": "Article 14",
        "reason": "",
    })
    assert result["category"] == "E"


@pytest.mark.parametrize("category", ["D1", "D2", "D3", "D4", "D5"])
def test_not_speaker_D_categories_not_forced(category):
    result = _classify({"category": category, "speaker_is_mp": False, "confidence": 80, "reason": ""})
    assert result["category"] == category


def test_not_speaker_E_stays_E():
    result = _classify({"category": "E", "speaker_is_mp": False, "confidence": 80, "reason": ""})
    assert result["category"] == "E"


# ---------------------------------------------------------------------------
# Guard 3: B/C _DATA_REQUIRED without source → force E
# ---------------------------------------------------------------------------

def test_data_required_set_contents():
    assert _DATA_REQUIRED == {"B1", "B2", "B3", "B4", "B5", "C1"}


@pytest.mark.parametrize("category", ["B1", "B2", "B3", "B4", "B5", "C1"])
def test_data_required_no_source_forced_to_E(category):
    result = _classify({
        "category": category,
        "speaker_is_mp": True,
        "confidence": 85,
        "data_contradicted": None,
        "constitutional_anchor": None,
        "reason": "",
    })
    assert result["category"] == "E"


@pytest.mark.parametrize("category", ["B1", "B2", "B3", "B4", "B5", "C1"])
def test_data_required_with_data_contradicted_passes(category):
    result = _classify({
        "category": category,
        "speaker_is_mp": True,
        "confidence": 85,
        "data_contradicted": "WHO 2023 report",
        "constitutional_anchor": None,
        "reason": "",
    })
    assert result["category"] == category


@pytest.mark.parametrize("category", ["B1", "C1"])
def test_data_required_with_constitutional_anchor_passes(category):
    result = _classify({
        "category": category,
        "speaker_is_mp": True,
        "confidence": 85,
        "data_contradicted": None,
        "constitutional_anchor": "Article 51A-h",
        "reason": "",
    })
    assert result["category"] == category


def test_C2_not_in_data_required_passes_without_source():
    result = _classify({
        "category": "C2",
        "speaker_is_mp": True,
        "confidence": 85,
        "data_contradicted": None,
        "constitutional_anchor": None,
        "reason": "",
    })
    assert result["category"] == "C2"


# ---------------------------------------------------------------------------
# Guard 4: invalid category → force E
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad_cat", ["A6", "B0", "a1", "", "NONE", "X1", "D6", "C4", "null", "undefined"])
def test_invalid_category_forced_to_E(bad_cat):
    result = _classify({"category": bad_cat, "speaker_is_mp": True, "confidence": 90, "reason": ""})
    assert result["category"] == "E"


# ---------------------------------------------------------------------------
# Happy paths — all guards pass
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("category", ["A1", "A2", "A3", "A4", "A5"])
def test_A_categories_pass_when_guards_satisfied(category):
    result = _classify({"category": category, "speaker_is_mp": True, "confidence": 80, "reason": ""})
    assert result["category"] == category


@pytest.mark.parametrize("category", ["D1", "D2", "D3", "D4", "D5"])
def test_D_categories_pass(category):
    result = _classify({"category": category, "speaker_is_mp": True, "confidence": 75, "reason": ""})
    assert result["category"] == category


def test_E_always_passes():
    result = _classify({"category": "E", "speaker_is_mp": True, "confidence": 100, "reason": ""})
    assert result["category"] == "E"


# ---------------------------------------------------------------------------
# Result structure
# ---------------------------------------------------------------------------

def test_result_defaults_populated():
    result = _classify({"category": "D1", "speaker_is_mp": True, "confidence": 80})
    assert result["constitutional_anchor"] is None
    assert result["data_contradicted"] is None
    assert result["reason"] == ""
    assert isinstance(result["confidence"], int)


def test_confidence_cast_to_int():
    result = _classify({"category": "D1", "speaker_is_mp": True, "confidence": "85"})
    assert result["confidence"] == 85
    assert isinstance(result["confidence"], int)


# ---------------------------------------------------------------------------
# category_group
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("category, group", [
    ("A1", "A"), ("A3", "A"), ("A5", "A"),
    ("B2", "B"), ("B5", "B"),
    ("C1", "C"), ("C3", "C"),
    ("D1", "D"), ("D5", "D"),
    ("E",  "E"),
])
def test_category_group_is_first_char(category, group):
    assert category[0] == group


# ---------------------------------------------------------------------------
# Attempt limit
# ---------------------------------------------------------------------------

def test_classify_returns_none_at_attempt_3():
    result = classify_statement("s", "c", "mp", "src", "2024-01-01", attempt=3)
    assert result is None


# ---------------------------------------------------------------------------
# extract_quotes
# ---------------------------------------------------------------------------

def test_extract_quotes_returns_empty_at_attempt_3():
    result = extract_quotes("text", "MP Name", attempt=3)
    assert result == []


def test_extract_quotes_returns_list_of_dicts():
    quotes_payload = {
        "quotes": [
            {"text": "We will fix this", "attribution": "said", "context": "about policy"},
            {"text": "This is wrong", "attribution": "claimed", "context": "in parliament"},
        ]
    }
    with patch("backend.agents.statement_agent._call_llm", return_value=json.dumps(quotes_payload)):
        result = extract_quotes("article text", "Rahul Gandhi")
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["text"] == "We will fix this"
    assert "attribution" in result[0]
    assert "context" in result[0]


def test_extract_quotes_caps_at_20():
    quotes_payload = {"quotes": [{"text": f"Quote {i}", "attribution": "said", "context": ""} for i in range(30)]}
    with patch("backend.agents.statement_agent._call_llm", return_value=json.dumps(quotes_payload)):
        result = extract_quotes("article text", "Test MP")
    assert len(result) == 20


def test_extract_quotes_empty_when_no_quotes():
    with patch("backend.agents.statement_agent._call_llm", return_value='{"quotes": []}'):
        result = extract_quotes("article text", "Test MP")
    assert result == []


def test_extract_quotes_strips_outer_quotes_from_text():
    payload = {"quotes": [{"text": '"actual quoted text"', "attribution": "said", "context": ""}]}
    with patch("backend.agents.statement_agent._call_llm", return_value=json.dumps(payload)):
        result = extract_quotes("text", "MP")
    assert result[0]["text"] == "actual quoted text"


def test_extract_quotes_skips_blank_text():
    payload = {"quotes": [{"text": "", "attribution": "said", "context": ""}]}
    with patch("backend.agents.statement_agent._call_llm", return_value=json.dumps(payload)):
        result = extract_quotes("text", "MP")
    assert result == []


# ---------------------------------------------------------------------------
# VALID_CATEGORIES
# ---------------------------------------------------------------------------

def test_valid_categories_complete():
    expected = {
        "A1", "A2", "A3", "A4", "A5",
        "B1", "B2", "B3", "B4", "B5",
        "C1", "C2", "C3",
        "D1", "D2", "D3", "D4", "D5",
        "E",
    }
    assert VALID_CATEGORIES == expected
