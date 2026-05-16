"""Tests for reqsnap.profiler."""

import json
from pathlib import Path

import pytest

from reqsnap.storage import save_snapshot
from reqsnap.profiler import (
    _body_size,
    profile_snapshot,
    profile_directory,
    format_profile_report,
    SnapshotProfile,
)


@pytest.fixture()
def snap_dir(tmp_path: Path) -> Path:
    return tmp_path


def _make_snap(method="GET", url="https://example.com/api", status=200, req_body=None, resp_body=None, elapsed=None):
    snap = {
        "request": {"method": method, "url": url, "headers": {}, "body": req_body},
        "response": {"status_code": status, "headers": {}, "body": resp_body, "elapsed_ms": elapsed},
    }
    return snap


# --- _body_size ---

def test_body_size_none():
    assert _body_size(None) == 0


def test_body_size_string():
    assert _body_size("hello") == 5


def test_body_size_bytes():
    assert _body_size(b"hello") == 5


def test_body_size_dict():
    data = {"key": "val"}
    assert _body_size(data) == len(json.dumps(data).encode())


# --- profile_snapshot ---

def test_profile_snapshot_returns_none_for_missing_key(snap_dir):
    result = profile_snapshot(snap_dir, "nonexistent-key")
    assert result is None


def test_profile_snapshot_basic_fields(snap_dir):
    snap = _make_snap(method="POST", url="https://api.test/v1", status=201, elapsed=42.5)
    save_snapshot(snap_dir, "mykey", snap)
    profile = profile_snapshot(snap_dir, "mykey")
    assert isinstance(profile, SnapshotProfile)
    assert profile.method == "POST"
    assert profile.url == "https://api.test/v1"
    assert profile.status_code == 201
    assert profile.response_time_ms == 42.5


def test_profile_snapshot_body_sizes(snap_dir):
    snap = _make_snap(req_body="hi", resp_body="hello world")
    save_snapshot(snap_dir, "bodykey", snap)
    profile = profile_snapshot(snap_dir, "bodykey")
    assert profile.request_body_bytes == 2
    assert profile.response_body_bytes == 11
    assert profile.total_bytes == 13


def test_profile_snapshot_no_elapsed(snap_dir):
    snap = _make_snap()
    save_snapshot(snap_dir, "notime", snap)
    profile = profile_snapshot(snap_dir, "notime")
    assert profile.response_time_ms is None


# --- profile_directory ---

def test_profile_directory_empty(snap_dir):
    assert profile_directory(snap_dir) == []


def test_profile_directory_multiple(snap_dir):
    for i in range(3):
        save_snapshot(snap_dir, f"key{i}", _make_snap(url=f"https://example.com/{i}"))
    profiles = profile_directory(snap_dir)
    assert len(profiles) == 3


# --- format_profile_report ---

def test_format_profile_report_empty():
    assert format_profile_report([]) == "No snapshots found."


def test_format_profile_report_contains_method(snap_dir):
    snap = _make_snap(method="DELETE", elapsed=10.0)
    save_snapshot(snap_dir, "delkey", snap)
    profiles = profile_directory(snap_dir)
    report = format_profile_report(profiles)
    assert "DELETE" in report


def test_format_profile_report_na_for_missing_time(snap_dir):
    save_snapshot(snap_dir, "notime2", _make_snap())
    profiles = profile_directory(snap_dir)
    report = format_profile_report(profiles)
    assert "n/a" in report
