"""Tests for reqsnap.matcher module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from reqsnap.matcher import _bodies_match, _normalize_headers, find_match, list_snapshots
from reqsnap.storage import save_snapshot


@pytest.fixture
def snap_dir(tmp_path: Path) -> Path:
    return tmp_path


_SAMPLE_SNAPSHOT = {
    "request": {"method": "GET", "url": "https://api.example.com/items", "headers": {}, "body": None},
    "response": {"status_code": 200, "headers": {"content-type": "application/json"}, "body": '{"items": []}'},
}


def test_normalize_headers_lowercases_keys():
    result = _normalize_headers({"Content-Type": "application/json", "X-Custom": "value"})
    assert result == {"content-type": "application/json", "x-custom": "value"}


def test_normalize_headers_none_returns_empty():
    assert _normalize_headers(None) == {}


def test_bodies_match_identical_strings():
    assert _bodies_match("hello", "hello") is True


def test_bodies_match_both_none():
    assert _bodies_match(None, None) is True


def test_bodies_match_json_equivalent():
    a = '{"b": 2, "a": 1}'
    b = '{"a": 1, "b": 2}'
    assert _bodies_match(a, b) is True


def test_bodies_match_one_none():
    assert _bodies_match(None, "something") is False
    assert _bodies_match("something", None) is False


def test_bodies_match_different_strings():
    assert _bodies_match("foo", "bar") is False


def test_find_match_exact(snap_dir: Path):
    save_snapshot(snap_dir, _SAMPLE_SNAPSHOT)
    result = find_match(snap_dir, "GET", "https://api.example.com/items")
    assert result is not None
    assert result["response"]["status_code"] == 200


def test_find_match_returns_none_when_missing(snap_dir: Path):
    result = find_match(snap_dir, "GET", "https://api.example.com/missing")
    assert result is None


def test_find_match_fallback_json_body(snap_dir: Path):
    snapshot = {
        "request": {"method": "POST", "url": "https://api.example.com/create", "headers": {}, "body": '{"a":1,"b":2}'},
        "response": {"status_code": 201, "headers": {}, "body": '{"id": 42}'},
    }
    save_snapshot(snap_dir, snapshot)
    # Same JSON content but different key order
    result = find_match(snap_dir, "POST", "https://api.example.com/create", body='{"b":2,"a":1}')
    assert result is not None
    assert result["response"]["status_code"] == 201


def test_list_snapshots_empty(snap_dir: Path):
    assert list_snapshots(snap_dir) == []


def test_list_snapshots_sorted(snap_dir: Path):
    for method, url in [("POST", "https://b.com"), ("GET", "https://a.com"), ("GET", "https://b.com")]:
        snap = {
            "request": {"method": method, "url": url, "headers": {}, "body": None},
            "response": {"status_code": 200, "headers": {}, "body": ""},
        }
        save_snapshot(snap_dir, snap)
    results = list_snapshots(snap_dir)
    urls = [s["request"]["url"] for s in results]
    assert urls == sorted(urls)
