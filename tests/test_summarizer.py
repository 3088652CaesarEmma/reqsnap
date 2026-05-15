"""Tests for reqsnap.summarizer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from reqsnap.storage import save_snapshot
from reqsnap.summarizer import (
    _method_counts,
    _status_counts,
    _unique_hosts,
    format_summary,
    summarize_directory,
)


@pytest.fixture()
def snap_dir(tmp_path: Path) -> Path:
    return tmp_path


def _make_snap(method: str, url: str, status: int) -> dict:
    return {
        "request": {"method": method, "url": url, "headers": {}, "body": None},
        "response": {"status_code": status, "headers": {}, "body": None},
    }


# ---------------------------------------------------------------------------
# _method_counts
# ---------------------------------------------------------------------------

def test_method_counts_single():
    snaps = [_make_snap("GET", "http://a.com/", 200)]
    assert _method_counts(snaps) == {"GET": 1}


def test_method_counts_multiple():
    snaps = [
        _make_snap("GET", "http://a.com/", 200),
        _make_snap("POST", "http://a.com/", 201),
        _make_snap("GET", "http://a.com/x", 200),
    ]
    counts = _method_counts(snaps)
    assert counts["GET"] == 2
    assert counts["POST"] == 1


def test_method_counts_empty():
    assert _method_counts([]) == {}


# ---------------------------------------------------------------------------
# _status_counts
# ---------------------------------------------------------------------------

def test_status_counts_groups_correctly():
    snaps = [
        _make_snap("GET", "http://a.com/", 200),
        _make_snap("GET", "http://a.com/", 200),
        _make_snap("GET", "http://a.com/", 404),
    ]
    counts = _status_counts(snaps)
    assert counts[200] == 2
    assert counts[404] == 1


# ---------------------------------------------------------------------------
# _unique_hosts
# ---------------------------------------------------------------------------

def test_unique_hosts_deduplicates():
    snaps = [
        _make_snap("GET", "https://api.example.com/v1/foo", 200),
        _make_snap("POST", "https://api.example.com/v1/bar", 201),
        _make_snap("GET", "https://other.io/path", 200),
    ]
    hosts = _unique_hosts(snaps)
    assert hosts == ["api.example.com", "other.io"]


def test_unique_hosts_empty():
    assert _unique_hosts([]) == []


# ---------------------------------------------------------------------------
# summarize_directory
# ---------------------------------------------------------------------------

def test_summarize_directory_empty(snap_dir):
    summary = summarize_directory(snap_dir)
    assert summary["total"] == 0
    assert summary["methods"] == {}
    assert summary["hosts"] == []


def test_summarize_directory_counts(snap_dir):
    for i, (method, status) in enumerate([("GET", 200), ("POST", 201), ("GET", 404)]):
        snap = _make_snap(method, f"https://example.com/res{i}", status)
        save_snapshot(snap_dir, f"key{i}", snap)

    summary = summarize_directory(snap_dir)
    assert summary["total"] == 3
    assert summary["methods"]["GET"] == 2
    assert summary["methods"]["POST"] == 1


# ---------------------------------------------------------------------------
# format_summary
# ---------------------------------------------------------------------------

def test_format_summary_contains_total():
    summary = {"total": 5, "methods": {"GET": 5}, "status_codes": {200: 5}, "hosts": ["a.com"]}
    text = format_summary(summary)
    assert "5" in text
    assert "GET=5" in text
    assert "200=5" in text
    assert "a.com" in text


def test_format_summary_no_hosts():
    summary = {"total": 0, "methods": {}, "status_codes": {}, "hosts": []}
    text = format_summary(summary)
    assert "(none)" in text
