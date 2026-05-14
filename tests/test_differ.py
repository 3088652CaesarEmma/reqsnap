"""Tests for reqsnap.differ."""

import pytest

from reqsnap.differ import diff_snapshots, is_identical, _diff_headers, _diff_body


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _snap(method="GET", url="https://example.com/api", req_headers=None,
          req_body=None, status=200, resp_headers=None, resp_body=None):
    return {
        "request": {
            "method": method,
            "url": url,
            "headers": req_headers or {},
            "body": req_body,
        },
        "response": {
            "status_code": status,
            "headers": resp_headers or {},
            "body": resp_body,
        },
    }


# ---------------------------------------------------------------------------
# _diff_headers
# ---------------------------------------------------------------------------

def test_diff_headers_identical_returns_empty():
    assert _diff_headers({"content-type": "application/json"}, {"content-type": "application/json"}) == []


def test_diff_headers_detects_changed_value():
    diffs = _diff_headers({"accept": "text/html"}, {"accept": "application/json"})
    assert len(diffs) == 1
    assert diffs[0]["header"] == "accept"


def test_diff_headers_detects_missing_key():
    diffs = _diff_headers({"x-token": "abc"}, {})
    assert diffs[0]["b"] is None


# ---------------------------------------------------------------------------
# _diff_body
# ---------------------------------------------------------------------------

def test_diff_body_identical_json_returns_none():
    assert _diff_body('{"a": 1}', '{"a": 1}') is None


def test_diff_body_different_json_returns_diff():
    result = _diff_body('{"a": 1}', '{"a": 2}')
    assert result is not None
    assert result["a"] == {"a": 1}
    assert result["b"] == {"a": 2}


def test_diff_body_both_none_returns_none():
    assert _diff_body(None, None) is None


# ---------------------------------------------------------------------------
# diff_snapshots
# ---------------------------------------------------------------------------

def test_identical_snapshots_empty_diff():
    snap = _snap()
    diff = diff_snapshots(snap, snap)
    assert is_identical(diff)


def test_method_change_detected():
    diff = diff_snapshots(_snap(method="GET"), _snap(method="POST"))
    assert "method" in diff["request"]
    assert diff["request"]["method"] == {"a": "GET", "b": "POST"}


def test_status_code_change_detected():
    diff = diff_snapshots(_snap(status=200), _snap(status=404))
    assert "status_code" in diff["response"]


def test_url_change_detected():
    diff = diff_snapshots(
        _snap(url="https://example.com/v1"),
        _snap(url="https://example.com/v2"),
    )
    assert "url" in diff["request"]


def test_response_body_change_detected():
    diff = diff_snapshots(
        _snap(resp_body='{"status": "ok"}'),
        _snap(resp_body='{"status": "error"}'),
    )
    assert "body" in diff["response"]


def test_is_identical_true_when_no_diffs():
    assert is_identical({"request": {}, "response": {}})


def test_is_identical_false_when_diffs_present():
    assert not is_identical({"request": {"method": {"a": "GET", "b": "POST"}}, "response": {}})
