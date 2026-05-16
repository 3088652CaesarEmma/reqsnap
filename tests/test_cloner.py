"""Tests for reqsnap.cloner."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from reqsnap.cloner import clone_snapshot, list_keys


@pytest.fixture()
def snap_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write_snap(snap_dir: Path, key: str, extra: dict | None = None) -> Path:
    data = {
        "key": key,
        "method": "GET",
        "url": "https://example.com/api",
        "request_headers": {},
        "request_body": None,
        "status_code": 200,
        "response_headers": {"content-type": "application/json"},
        "response_body": '{"ok": true}',
    }
    if extra:
        data.update(extra)
    path = snap_dir / f"{key}.json"
    path.write_text(json.dumps(data))
    return path


# ---------------------------------------------------------------------------
# list_keys
# ---------------------------------------------------------------------------

def test_list_keys_empty(snap_dir: Path) -> None:
    assert list_keys(snap_dir) == []


def test_list_keys_returns_stems(snap_dir: Path) -> None:
    _write_snap(snap_dir, "alpha")
    _write_snap(snap_dir, "beta")
    assert set(list_keys(snap_dir)) == {"alpha", "beta"}


# ---------------------------------------------------------------------------
# clone_snapshot — happy paths
# ---------------------------------------------------------------------------

def test_clone_creates_destination_file(snap_dir: Path) -> None:
    _write_snap(snap_dir, "original")
    dest = clone_snapshot(snap_dir, "original", "copy")
    assert dest.exists()


def test_clone_updates_key_field(snap_dir: Path) -> None:
    _write_snap(snap_dir, "original")
    clone_snapshot(snap_dir, "original", "copy")
    data = json.loads((snap_dir / "copy.json").read_text())
    assert data["key"] == "copy"


def test_clone_preserves_other_fields(snap_dir: Path) -> None:
    _write_snap(snap_dir, "original")
    clone_snapshot(snap_dir, "original", "copy")
    data = json.loads((snap_dir / "copy.json").read_text())
    assert data["method"] == "GET"
    assert data["status_code"] == 200


def test_clone_does_not_mutate_source(snap_dir: Path) -> None:
    _write_snap(snap_dir, "original")
    clone_snapshot(snap_dir, "original", "copy")
    src = json.loads((snap_dir / "original.json").read_text())
    assert src["key"] == "original"


def test_clone_overwrite_replaces_existing(snap_dir: Path) -> None:
    _write_snap(snap_dir, "original")
    _write_snap(snap_dir, "copy", extra={"status_code": 404})
    clone_snapshot(snap_dir, "original", "copy", overwrite=True)
    data = json.loads((snap_dir / "copy.json").read_text())
    assert data["status_code"] == 200


# ---------------------------------------------------------------------------
# clone_snapshot — error paths
# ---------------------------------------------------------------------------

def test_clone_missing_source_raises(snap_dir: Path) -> None:
    with pytest.raises(FileNotFoundError, match="missing_key"):
        clone_snapshot(snap_dir, "missing_key", "dest")


def test_clone_existing_dest_raises_without_overwrite(snap_dir: Path) -> None:
    _write_snap(snap_dir, "original")
    _write_snap(snap_dir, "copy")
    with pytest.raises(FileExistsError, match="copy"):
        clone_snapshot(snap_dir, "original", "copy")
