"""Tests for reqsnap.exporter — HAR export functionality."""

import json
import pytest
from pathlib import Path

from reqsnap.storage import save_snapshot
from reqsnap.exporter import export_har, export_har_file, _snapshot_to_har_entry


SAMPLE_SNAP = {
    "recorded_at": "2024-01-15T12:00:00Z",
    "request": {
        "method": "POST",
        "url": "https://api.example.com/data",
        "headers": {"content-type": "application/json"},
        "body": '{"hello": "world"}',
    },
    "response": {
        "status_code": 201,
        "headers": {"content-type": "application/json"},
        "body": '{"id": 42}',
        "elapsed_ms": 120,
    },
}


@pytest.fixture()
def snap_dir(tmp_path):
    return tmp_path / "snaps"


def test_snapshot_to_har_entry_structure():
    entry = _snapshot_to_har_entry(SAMPLE_SNAP)
    assert entry["request"]["method"] == "POST"
    assert entry["request"]["url"] == "https://api.example.com/data"
    assert entry["response"]["status"] == 201
    assert entry["time"] == 120
    assert entry["startedDateTime"] == "2024-01-15T12:00:00Z"


def test_snapshot_to_har_entry_request_headers():
    entry = _snapshot_to_har_entry(SAMPLE_SNAP)
    headers = entry["request"]["headers"]
    assert any(h["name"] == "content-type" for h in headers)


def test_snapshot_to_har_entry_post_data():
    entry = _snapshot_to_har_entry(SAMPLE_SNAP)
    assert entry["request"]["postData"] is not None
    assert entry["request"]["postData"]["text"] == '{"hello": "world"}'


def test_snapshot_to_har_entry_no_body():
    snap = {**SAMPLE_SNAP, "request": {**SAMPLE_SNAP["request"], "body": None}}
    entry = _snapshot_to_har_entry(snap)
    assert entry["request"]["postData"] is None
    assert entry["request"]["bodySize"] == 0


def test_export_har_empty_dir(snap_dir):
    snap_dir.mkdir()
    har = export_har(snap_dir)
    assert har["log"]["version"] == "1.2"
    assert har["log"]["entries"] == []


def test_export_har_with_snapshots(snap_dir):
    snap_dir.mkdir()
    save_snapshot(snap_dir, "key-abc", SAMPLE_SNAP)
    har = export_har(snap_dir)
    assert len(har["log"]["entries"]) == 1
    assert har["log"]["entries"][0]["response"]["status"] == 201


def test_export_har_filters_by_keys(snap_dir):
    snap_dir.mkdir()
    save_snapshot(snap_dir, "key-abc", SAMPLE_SNAP)
    save_snapshot(snap_dir, "key-xyz", SAMPLE_SNAP)
    har = export_har(snap_dir, keys=["key-abc"])
    assert len(har["log"]["entries"]) == 1


def test_export_har_skips_missing_key(snap_dir):
    snap_dir.mkdir()
    har = export_har(snap_dir, keys=["does-not-exist"])
    assert har["log"]["entries"] == []


def test_export_har_file_writes_json(snap_dir, tmp_path):
    snap_dir.mkdir()
    save_snapshot(snap_dir, "key-abc", SAMPLE_SNAP)
    out = tmp_path / "output.har"
    count = export_har_file(snap_dir, out)
    assert count == 1
    data = json.loads(out.read_text())
    assert "log" in data
    assert len(data["log"]["entries"]) == 1


def test_export_har_creator_metadata(snap_dir):
    snap_dir.mkdir()
    har = export_har(snap_dir)
    creator = har["log"]["creator"]
    assert creator["name"] == "reqsnap"
