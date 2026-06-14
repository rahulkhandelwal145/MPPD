"""Tests for backend/scraper/news.py — Phase 4 news scraper.

All external I/O (feedparser, googlenewsdecoder, httpx) is mocked.
"""

import time
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from backend.scraper.news import (
    TRUSTED_DOMAINS,
    entry_source_domain,
    extract_domain,
    fetch_article,
    fetch_rss,
    filter_by_whitelist,
    html_to_text,
    parse_date,
    resolve_article_url,
)


# ---------------------------------------------------------------------------
# extract_domain
# ---------------------------------------------------------------------------

def test_extract_domain_strips_www():
    assert extract_domain("https://www.thehindu.com/article") == "thehindu.com"


def test_extract_domain_no_www():
    assert extract_domain("https://thewire.in/politics/article") == "thewire.in"


def test_extract_domain_none_returns_empty():
    assert extract_domain(None) == ""


def test_extract_domain_empty_string_returns_empty():
    assert extract_domain("") == ""


def test_extract_domain_lowercases():
    assert extract_domain("https://TheHindu.COM/article") == "thehindu.com"


def test_extract_domain_subdomain_preserved():
    assert extract_domain("https://timesofindia.indiatimes.com/article") == "timesofindia.indiatimes.com"


# ---------------------------------------------------------------------------
# entry_source_domain
# ---------------------------------------------------------------------------

def _entry(source_href=None, link=None):
    e = SimpleNamespace()
    e.source = {"href": source_href} if source_href is not None else None
    e.link = link
    return e


def test_entry_source_domain_prefers_source_href():
    e = _entry(source_href="https://thehindu.com/", link="https://news.google.com/encrypted")
    assert entry_source_domain(e) == "thehindu.com"


def test_entry_source_domain_falls_back_to_link():
    e = _entry(source_href=None, link="https://indianexpress.com/article")
    assert entry_source_domain(e) == "indianexpress.com"


def test_entry_source_domain_empty_href_falls_back_to_link():
    e = _entry(source_href="", link="https://ndtv.com/news")
    assert entry_source_domain(e) == "ndtv.com"


def test_entry_source_domain_source_as_object():
    source_obj = SimpleNamespace(href="https://scroll.in/article")
    e = SimpleNamespace(source=source_obj, link=None)
    assert entry_source_domain(e) == "scroll.in"


def test_entry_source_domain_no_source_no_link():
    e = SimpleNamespace(source=None, link=None)
    assert entry_source_domain(e) == ""


# ---------------------------------------------------------------------------
# TRUSTED_DOMAINS whitelist
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("domain", [
    "thehindu.com",
    "indianexpress.com",
    "ndtv.com",
    "hindustantimes.com",
    "thewire.in",
    "scroll.in",
    "theprint.in",
    "telegraphindia.com",
    "livemint.com",
    "businessstandard.com",
    "timesofindia.indiatimes.com",
    "deccanherald.com",
    "tribuneindia.com",
    "thequint.com",
    "newslaundry.com",
])
def test_trusted_domain_present(domain):
    assert domain in TRUSTED_DOMAINS


def test_bbc_not_trusted():
    assert "bbc.com" not in TRUSTED_DOMAINS


def test_whitelist_has_15_entries():
    assert len(TRUSTED_DOMAINS) == 15


# ---------------------------------------------------------------------------
# filter_by_whitelist
# ---------------------------------------------------------------------------

def test_filter_whitelist_trusted_passes():
    entries = [_entry(source_href="https://thehindu.com/")]
    assert len(filter_by_whitelist(entries)) == 1


def test_filter_whitelist_untrusted_removed():
    entries = [_entry(source_href="https://bbc.com/")]
    assert filter_by_whitelist(entries) == []


def test_filter_whitelist_mixed():
    entries = [
        _entry(source_href="https://thehindu.com/"),
        _entry(source_href="https://bbc.com/"),
        _entry(source_href="https://ndtv.com/"),
    ]
    result = filter_by_whitelist(entries)
    assert len(result) == 2


def test_filter_whitelist_empty_list():
    assert filter_by_whitelist([]) == []


# ---------------------------------------------------------------------------
# parse_date
# ---------------------------------------------------------------------------

def test_parse_date_struct_time_to_datetime():
    st = time.struct_time((2024, 3, 15, 10, 30, 0, 4, 75, 0))
    result = parse_date(st)
    assert isinstance(result, datetime)
    assert result.year == 2024
    assert result.month == 3
    assert result.day == 15


def test_parse_date_none_returns_none():
    assert parse_date(None) is None


def test_parse_date_string_returns_none():
    assert parse_date("2024-03-15") is None


# ---------------------------------------------------------------------------
# fetch_rss  (mocked feedparser)
# ---------------------------------------------------------------------------

def _fake_feed(entries):
    feed = MagicMock()
    feed.entries = entries
    feed.bozo = False
    feed.bozo_exception = None
    return feed


def test_fetch_rss_returns_entries():
    entries = [MagicMock(), MagicMock()]
    with patch("backend.scraper.news.feedparser.parse", return_value=_fake_feed(entries)) as mock_parse:
        result = fetch_rss("Rahul Gandhi")
    assert result is entries
    call_url = mock_parse.call_args[0][0]
    assert "Rahul" in call_url


def test_fetch_rss_empty_feed_returns_empty():
    with patch("backend.scraper.news.feedparser.parse", return_value=_fake_feed([])):
        assert fetch_rss("Unknown MP") == []


def test_fetch_rss_url_includes_gl_IN():
    with patch("backend.scraper.news.feedparser.parse", return_value=_fake_feed([])) as mock_parse:
        fetch_rss("Narendra Modi")
    assert "IN" in mock_parse.call_args[0][0]


def test_fetch_rss_bozo_feed_still_returns_entries():
    entries = [MagicMock()]
    feed = _fake_feed(entries)
    feed.bozo = True
    feed.bozo_exception = Exception("parse error")
    with patch("backend.scraper.news.feedparser.parse", return_value=feed):
        result = fetch_rss("Test MP")
    assert result is entries


# ---------------------------------------------------------------------------
# resolve_article_url  (mocked gnewsdecoder)
# ---------------------------------------------------------------------------

def test_resolve_article_url_success():
    e = SimpleNamespace(link="https://news.google.com/encrypted", title="Test")
    mock_result = {"status": True, "decoded_url": "https://thehindu.com/article"}
    with patch("backend.scraper.news.gnewsdecoder", return_value=mock_result):
        assert resolve_article_url(e, "Test MP") == "https://thehindu.com/article"


def test_resolve_article_url_status_false_returns_none():
    e = SimpleNamespace(link="https://news.google.com/encrypted", title="Test")
    with patch("backend.scraper.news.gnewsdecoder", return_value={"status": False, "decoded_url": None}):
        assert resolve_article_url(e, "Test MP") is None


def test_resolve_article_url_exception_returns_none():
    e = SimpleNamespace(link="https://news.google.com/encrypted", title="Test")
    with patch("backend.scraper.news.gnewsdecoder", side_effect=Exception("network error")):
        assert resolve_article_url(e, "Test MP") is None


def test_resolve_article_url_no_link_returns_none():
    e = SimpleNamespace(link=None, title="No Link")
    assert resolve_article_url(e, "Test MP") is None


def test_resolve_article_url_missing_link_attr_returns_none():
    e = SimpleNamespace(title="No Link Attr")
    assert resolve_article_url(e, "Test MP") is None


# ---------------------------------------------------------------------------
# fetch_article  (mocked httpx)
# ---------------------------------------------------------------------------

def _mock_httpx_client(text, content_type="text/html", raise_exc=None):
    resp = MagicMock()
    resp.text = text
    resp.headers = {"content-type": content_type}
    resp.raise_for_status = MagicMock()
    if raise_exc:
        resp.raise_for_status.side_effect = raise_exc

    client = MagicMock()
    client.__enter__ = MagicMock(return_value=client)
    client.__exit__ = MagicMock(return_value=False)
    client.get = MagicMock(return_value=resp)
    return client


def test_fetch_article_html_returns_text():
    client = _mock_httpx_client("<html><body><p>Hello</p></body></html>")
    with patch("backend.scraper.news.httpx.Client", return_value=client):
        result = fetch_article("https://thehindu.com/article")
    assert "Hello" in result


def test_fetch_article_non_html_returns_none():
    client = _mock_httpx_client("binary", content_type="application/pdf")
    with patch("backend.scraper.news.httpx.Client", return_value=client):
        assert fetch_article("https://example.com/file.pdf") is None


def test_fetch_article_text_plain_accepted():
    client = _mock_httpx_client("plain text content", content_type="text/plain")
    with patch("backend.scraper.news.httpx.Client", return_value=client):
        result = fetch_article("https://example.com/article.txt")
    assert result == "plain text content"


def test_fetch_article_http_error_returns_none():
    import httpx as _httpx
    client = MagicMock()
    client.__enter__ = MagicMock(return_value=client)
    client.__exit__ = MagicMock(return_value=False)
    client.get = MagicMock(side_effect=_httpx.HTTPError("connection refused"))
    with patch("backend.scraper.news.httpx.Client", return_value=client):
        assert fetch_article("https://example.com/broken") is None


# ---------------------------------------------------------------------------
# html_to_text
# ---------------------------------------------------------------------------

def test_html_to_text_extracts_paragraphs():
    html = "<html><body><p>First paragraph about Indian politics today in Parliament.</p></body></html>"
    result = html_to_text(html)
    assert "First paragraph" in result


def test_html_to_text_strips_script():
    html = "<html><body><script>alert('xss');</script><p>Real content that is longer than 40 characters here.</p></body></html>"
    result = html_to_text(html)
    assert "alert" not in result
    assert "Real content" in result


def test_html_to_text_strips_nav_and_footer():
    html = "<html><nav>Menu items</nav><body><p>Article paragraph content that is long enough to pass.</p></body><footer>Copyright 2024</footer></html>"
    result = html_to_text(html)
    assert "Copyright 2024" not in result
    assert "Article paragraph" in result


def test_html_to_text_filters_short_paragraphs():
    html = "<html><body><p>Short.</p><p>This is a much longer paragraph that easily exceeds forty characters in length.</p></body></html>"
    result = html_to_text(html)
    assert "Short." not in result
    assert "much longer paragraph" in result


def test_html_to_text_truncates_at_8000():
    big_para = "<p>" + ("A" * 200) + "</p>"
    html = "<html><body>" + big_para * 50 + "</body></html>"
    result = html_to_text(html)
    assert len(result) <= 8000


def test_html_to_text_no_triple_newlines():
    html = "<html><body><p>First long enough paragraph content here for the test.</p><p>Second long enough paragraph content here for the test.</p></body></html>"
    result = html_to_text(html)
    assert "\n\n\n" not in result


def test_html_to_text_returns_string():
    assert isinstance(html_to_text("<html><body></body></html>"), str)
