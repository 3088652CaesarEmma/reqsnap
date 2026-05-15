"""Tests for reqsnap.inspector."""
import json
from pathlib import Path

import pytest

from reqsnap.inspector import summarise_snapshot, validate_snapshot
from reqsnap.storage import save_snapshot


@pytest.fixture()
def snap_dir(tmp_path: Path) -> Path:
    return tmp_path


def _save(snap_dir: Path, snap: dict) -> Path:
    """Persist *snap* and return its path."""
    from reqsnap.storage import snapshot_path

    req = snap["request"]
    p = snapshot_path(snap_dir, req["method"], req["url"], req.get("body"))
    save_snapshot(p, snap)
    return p


_BASE = {
    "request": {
        "method": "GET",
        "url": "https://api.example.com/items",
        "headers": {"Accept": "application/json"},
        "body": None,
    },
    "response": {
        "status_code": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"items": []}),
    },
}


def test_summarise_returns_method_and_url(snap_dir):
    p = _save(snap_dir, _BASE)
    summary = summarise_snapshot(p)
    assert summary["method"] == "GET"
    assert summary["url"] == "https://api.example.com/items"


def test_summarise_status_code(snap_dir):
    p = _save(snap_dir, _BASE)
    summary = summarise_snapshot(p)
    assert summary["status"] == 200


def test_summarise_json_flags(snap_dir):
    p = _save(snap_dir, _BASE)
    summary = summarise_snapshot(p)
    assert summary["response_is_json"] is True
    assert summary["request_is_json"] is False


def test_summarise_body_bytes(snap_dir):
    p = _save(snap_dir, _BASE)
    summary = summarise_snapshot(p)
    expected = len(json.dumps({"items": []}).encode())
    assert summary["response_body_bytes"] == expected


def test_validate_clean_snapshot_no_warnings(snap_dir):
    p = _save(snap_dir, _BASE)
    assert validate_snapshot(p) == []


def test_validate_missing_method(snap_dir):
    snap = json.loads(json.dumps(_BASE))
    del snap["request"]["method"]
    p = _save(snap_dir, snap)
    warnings = validate_snapshot(p)
    assert any("method" in w for w in warnings)


def test_validate_invalid_status_code(snap_dir):
    snap = json.loads(json.dumps(_BASE))
    snap["response"]["status_code"] = 9999
    p = _save(snap_dir, snap)
    warnings = validate_snapshot(p)
    assert any("status_code" in w for w in warnings)


def test_validate_bad_json_body(snap_dir):
    snap = json.loads(json.dumps(_BASE))
    snap["response"]["body"] = "not-json-at-all"
    p = _save(snap_dir, snap)
    warnings = validate_snapshot(p)
    assert any("JSON" in w for w in warnings)


def test_validate_missing_response_section(snap_dir):
    snap = {"request": _BASE["request"]}
    p = _save(snap_dir, snap)
    warnings = validate_snapshot(p)
    assert any("response" in w.lower() for w in warnings)
