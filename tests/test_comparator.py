"""Tests for reqsnap.comparator."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from reqsnap.comparator import compare_snapshots, CompareReport


@pytest.fixture()
def snap_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(snap_dir: Path, key: str, data: dict) -> None:
    (snap_dir / f"{key}.json").write_text(json.dumps(data))


def _base_snap(**overrides) -> dict:
    snap = {
        "key": "k",
        "method": "GET",
        "url": "https://example.com/api",
        "status_code": 200,
        "request_headers": {"Accept": "application/json"},
        "response_headers": {"Content-Type": "application/json"},
        "request_body": None,
        "response_body": '{"ok": true}',
    }
    snap.update(overrides)
    return snap


def test_identical_snapshots(snap_dir: Path) -> None:
    snap = _base_snap(key="a")
    _write(snap_dir, "a", snap)
    _write(snap_dir, "b", {**snap, "key": "b"})
    report = compare_snapshots(snap_dir, "a", "b")
    assert report.is_identical
    assert not report.differing_fields
    assert not report.only_in_a
    assert not report.only_in_b


def test_differing_method(snap_dir: Path) -> None:
    _write(snap_dir, "a", _base_snap(key="a", method="GET"))
    _write(snap_dir, "b", _base_snap(key="b", method="POST"))
    report = compare_snapshots(snap_dir, "a", "b")
    assert "method" in report.differing_fields
    assert report.differing_fields["method"] == {"a": "GET", "b": "POST"}


def test_differing_status_code(snap_dir: Path) -> None:
    _write(snap_dir, "a", _base_snap(key="a", status_code=200))
    _write(snap_dir, "b", _base_snap(key="b", status_code=404))
    report = compare_snapshots(snap_dir, "a", "b")
    assert "status_code" in report.differing_fields


def test_matching_fields_listed(snap_dir: Path) -> None:
    _write(snap_dir, "a", _base_snap(key="a"))
    _write(snap_dir, "b", _base_snap(key="b", status_code=404))
    report = compare_snapshots(snap_dir, "a", "b")
    assert "method" in report.matching_fields
    assert "url" in report.matching_fields


def test_header_only_in_a(snap_dir: Path) -> None:
    _write(snap_dir, "a", _base_snap(key="a", request_headers={"X-Token": "abc"}))
    _write(snap_dir, "b", _base_snap(key="b", request_headers={}))
    report = compare_snapshots(snap_dir, "a", "b")
    assert any("x-token" in f for f in report.only_in_a)


def test_header_only_in_b(snap_dir: Path) -> None:
    _write(snap_dir, "a", _base_snap(key="a", request_headers={}))
    _write(snap_dir, "b", _base_snap(key="b", request_headers={"X-Token": "abc"}))
    report = compare_snapshots(snap_dir, "a", "b")
    assert any("x-token" in f for f in report.only_in_b)


def test_missing_snapshot_raises(snap_dir: Path) -> None:
    _write(snap_dir, "a", _base_snap(key="a"))
    with pytest.raises(FileNotFoundError):
        compare_snapshots(snap_dir, "a", "missing")


def test_report_keys_stored(snap_dir: Path) -> None:
    _write(snap_dir, "x", _base_snap(key="x"))
    _write(snap_dir, "y", _base_snap(key="y"))
    report = compare_snapshots(snap_dir, "x", "y")
    assert report.key_a == "x"
    assert report.key_b == "y"


def test_is_identical_false_when_diff(snap_dir: Path) -> None:
    _write(snap_dir, "a", _base_snap(key="a", url="https://a.com"))
    _write(snap_dir, "b", _base_snap(key="b", url="https://b.com"))
    report = compare_snapshots(snap_dir, "a", "b")
    assert not report.is_identical
