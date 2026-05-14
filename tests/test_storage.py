"""Tests for reqsnap.storage module."""

import json
import os
import tempfile
import pytest

from reqsnap.storage import save_snapshot, load_snapshot, snapshot_path, _make_key


@pytest.fixture
def snap_dir(tmp_path):
    return str(tmp_path / "snapshots")


def test_make_key_deterministic():
    key1 = _make_key("GET", "https://example.com/api")
    key2 = _make_key("GET", "https://example.com/api")
    assert key1 == key2


def test_make_key_differs_by_method():
    assert _make_key("GET", "https://example.com") != _make_key("POST", "https://example.com")


def test_make_key_differs_by_body():
    key_no_body = _make_key("POST", "https://example.com", None)
    key_with_body = _make_key("POST", "https://example.com", b"{\"x\": 1}")
    assert key_no_body != key_with_body


def test_save_and_load_snapshot(snap_dir):
    response = {"status_code": 200, "headers": {"Content-Type": "application/json"}, "body": "{\"ok\": true}"}
    path = save_snapshot("GET", "https://api.example.com/items", response, snapshot_dir=snap_dir)

    assert os.path.exists(path)
    record = load_snapshot("GET", "https://api.example.com/items", snapshot_dir=snap_dir)
    assert record is not None
    assert record["method"] == "GET"
    assert record["url"] == "https://api.example.com/items"
    assert record["response"]["status_code"] == 200
    assert "recorded_at" in record


def test_load_missing_snapshot_returns_none(snap_dir):
    result = load_snapshot("DELETE", "https://api.example.com/missing", snapshot_dir=snap_dir)
    assert result is None


def test_snapshot_dir_created_automatically(tmp_path):
    new_dir = str(tmp_path / "deep" / "nested" / "snaps")
    response = {"status_code": 204, "headers": {}, "body": ""}
    save_snapshot("DELETE", "https://example.com/res/1", response, snapshot_dir=new_dir)
    assert os.path.isdir(new_dir)


def test_saved_file_is_valid_json(snap_dir):
    response = {"status_code": 200, "headers": {}, "body": "hello"}
    path = save_snapshot("GET", "https://example.com", response, snapshot_dir=snap_dir)
    with open(path) as f:
        data = json.load(f)
    assert data["response"]["body"] == "hello"
