"""Tests for reqsnap.renamer and reqsnap.cli_renamer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from reqsnap.renamer import list_keys, rename_snapshot
from reqsnap.storage import snapshot_path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture()
def snap_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write_snap(snap_dir: Path, key: str, url: str = "https://example.com") -> Path:
    path = snapshot_path(snap_dir, key)
    data = {
        "key": key,
        "method": "GET",
        "url": url,
        "status_code": 200,
        "response_body": "ok",
    }
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# rename_snapshot
# ---------------------------------------------------------------------------

def test_rename_moves_file(snap_dir: Path) -> None:
    _write_snap(snap_dir, "old-key")
    rename_snapshot(snap_dir, "old-key", "new-key")
    assert not snapshot_path(snap_dir, "old-key").exists()
    assert snapshot_path(snap_dir, "new-key").exists()


def test_rename_updates_key_field(snap_dir: Path) -> None:
    _write_snap(snap_dir, "alpha")
    rename_snapshot(snap_dir, "alpha", "beta")
    data = json.loads(snapshot_path(snap_dir, "beta").read_text())
    assert data["key"] == "beta"


def test_rename_missing_key_raises(snap_dir: Path) -> None:
    with pytest.raises(FileNotFoundError, match="ghost"):
        rename_snapshot(snap_dir, "ghost", "new-ghost")


def test_rename_existing_destination_raises(snap_dir: Path) -> None:
    _write_snap(snap_dir, "src")
    _write_snap(snap_dir, "dst")
    with pytest.raises(FileExistsError, match="dst"):
        rename_snapshot(snap_dir, "src", "dst")


def test_rename_moves_sidecar_files(snap_dir: Path) -> None:
    _write_snap(snap_dir, "snap-a")
    old_stem = snapshot_path(snap_dir, "snap-a").stem
    sidecar = snap_dir / f"{old_stem}.tags.json"
    sidecar.write_text(json.dumps(["important"]), encoding="utf-8")

    rename_snapshot(snap_dir, "snap-a", "snap-b")

    new_stem = snapshot_path(snap_dir, "snap-b").stem
    assert not sidecar.exists()
    assert (snap_dir / f"{new_stem}.tags.json").exists()


# ---------------------------------------------------------------------------
# list_keys
# ---------------------------------------------------------------------------

def test_list_keys_empty_directory(snap_dir: Path) -> None:
    assert list_keys(snap_dir) == []


def test_list_keys_returns_all_keys(snap_dir: Path) -> None:
    _write_snap(snap_dir, "key-one")
    _write_snap(snap_dir, "key-two")
    keys = list_keys(snap_dir)
    assert "key-one" in keys
    assert "key-two" in keys
    assert len(keys) == 2


def test_list_keys_skips_invalid_json(snap_dir: Path) -> None:
    _write_snap(snap_dir, "valid")
    (snap_dir / "broken.json").write_text("not-json", encoding="utf-8")
    keys = list_keys(snap_dir)
    assert len(keys) == 1
    assert "valid" in keys
