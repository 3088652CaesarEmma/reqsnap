"""Tests for reqsnap.grouper."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from reqsnap.grouper import format_groups, group_snapshots


@pytest.fixture()
def snap_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(snap_dir: Path, key: str, snap: dict) -> None:
    snap.setdefault("key", key)
    (snap_dir / f"{key}.json").write_text(json.dumps(snap))


def _base(method="GET", url="https://api.example.com/v1", status=200):
    return {
        "method": method,
        "url": url,
        "response": {"status_code": status, "headers": {}, "body": None},
    }


# ---------------------------------------------------------------------------
# group_snapshots
# ---------------------------------------------------------------------------

def test_group_by_host_single(snap_dir):
    _write(snap_dir, "a", _base(url="https://api.example.com/v1"))
    groups = group_snapshots(snap_dir, by="host")
    assert "api.example.com" in groups
    assert "a" in groups["api.example.com"]


def test_group_by_host_multiple_hosts(snap_dir):
    _write(snap_dir, "a", _base(url="https://api.example.com/"))
    _write(snap_dir, "b", _base(url="https://other.io/data"))
    groups = group_snapshots(snap_dir, by="host")
    assert set(groups.keys()) == {"api.example.com", "other.io"}


def test_group_by_method(snap_dir):
    _write(snap_dir, "g", _base(method="GET"))
    _write(snap_dir, "p", _base(method="POST"))
    groups = group_snapshots(snap_dir, by="method")
    assert "GET" in groups
    assert "POST" in groups


def test_group_by_status(snap_dir):
    _write(snap_dir, "ok", _base(status=200))
    _write(snap_dir, "err", _base(status=404))
    groups = group_snapshots(snap_dir, by="status")
    assert "200" in groups
    assert "404" in groups


def test_group_empty_directory(snap_dir):
    groups = group_snapshots(snap_dir, by="host")
    assert groups == {}


def test_group_invalid_dimension_raises(snap_dir):
    with pytest.raises(ValueError, match="Unknown dimension"):
        group_snapshots(snap_dir, by="banana")


def test_group_missing_url_uses_unknown(snap_dir):
    snap = {"method": "GET", "response": {"status_code": 200}}
    (snap_dir / "x.json").write_text(json.dumps(snap))
    groups = group_snapshots(snap_dir, by="host")
    assert "unknown" in groups


def test_group_corrupt_file_skipped(snap_dir):
    (snap_dir / "bad.json").write_text("not-json")
    _write(snap_dir, "good", _base())
    groups = group_snapshots(snap_dir, by="method")
    assert "GET" in groups


# ---------------------------------------------------------------------------
# format_groups
# ---------------------------------------------------------------------------

def test_format_groups_empty():
    assert format_groups({}) == "(no snapshots)"


def test_format_groups_contains_label():
    output = format_groups({"api.example.com": ["snap1", "snap2"]})
    assert "api.example.com (2)" in output
    assert "snap1" in output
    assert "snap2" in output


def test_format_groups_sorted_labels():
    groups = {"z-host": ["z"], "a-host": ["a"]}
    output = format_groups(groups)
    assert output.index("a-host") < output.index("z-host")
