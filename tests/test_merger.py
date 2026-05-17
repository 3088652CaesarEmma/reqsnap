"""Tests for reqsnap.merger."""

import json
import pytest
from pathlib import Path

from reqsnap.merger import merge_directories, list_conflicts


@pytest.fixture()
def snap_dir(tmp_path: Path):
    src = tmp_path / "source"
    dst = tmp_path / "dest"
    src.mkdir()
    dst.mkdir()
    return src, dst


def _write(directory: Path, stem: str, data: dict) -> Path:
    p = directory / f"{stem}.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def _read(directory: Path, stem: str) -> dict:
    return json.loads((directory / f"{stem}.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# list_conflicts
# ---------------------------------------------------------------------------

def test_list_conflicts_no_overlap(snap_dir):
    src, dst = snap_dir
    _write(src, "snap_a", {"key": "snap_a"})
    _write(dst, "snap_b", {"key": "snap_b"})
    assert list_conflicts(src, dst) == []


def test_list_conflicts_detects_shared_stem(snap_dir):
    src, dst = snap_dir
    _write(src, "snap_a", {"key": "snap_a"})
    _write(dst, "snap_a", {"key": "snap_a"})
    assert list_conflicts(src, dst) == ["snap_a"]


# ---------------------------------------------------------------------------
# merge_directories — no conflicts
# ---------------------------------------------------------------------------

def test_merge_copies_new_snapshots(snap_dir):
    src, dst = snap_dir
    _write(src, "snap_a", {"key": "snap_a", "method": "GET"})
    copied, skipped, renamed = merge_directories(src, dst)
    assert copied == 1
    assert skipped == 0
    assert renamed == 0
    assert (dst / "snap_a.json").exists()


def test_merge_creates_dest_if_missing(tmp_path):
    src = tmp_path / "source"
    dst = tmp_path / "new_dest"
    src.mkdir()
    _write(src, "snap_x", {"key": "snap_x"})
    merge_directories(src, dst)
    assert dst.is_dir()


# ---------------------------------------------------------------------------
# merge_directories — keep_dest (default)
# ---------------------------------------------------------------------------

def test_conflict_keep_dest_preserves_dest(snap_dir):
    src, dst = snap_dir
    _write(src, "snap_a", {"key": "snap_a", "method": "POST"})
    _write(dst, "snap_a", {"key": "snap_a", "method": "GET"})
    copied, skipped, _ = merge_directories(src, dst, strategy="keep_dest")
    assert skipped == 1
    assert _read(dst, "snap_a")["method"] == "GET"


# ---------------------------------------------------------------------------
# merge_directories — keep_source
# ---------------------------------------------------------------------------

def test_conflict_keep_source_overwrites_dest(snap_dir):
    src, dst = snap_dir
    _write(src, "snap_a", {"key": "snap_a", "method": "POST"})
    _write(dst, "snap_a", {"key": "snap_a", "method": "GET"})
    copied, skipped, _ = merge_directories(src, dst, strategy="keep_source")
    assert copied == 1
    assert _read(dst, "snap_a")["method"] == "POST"


# ---------------------------------------------------------------------------
# merge_directories — keep_both
# ---------------------------------------------------------------------------

def test_conflict_keep_both_creates_merged_file(snap_dir):
    src, dst = snap_dir
    _write(src, "snap_a", {"key": "snap_a", "method": "POST"})
    _write(dst, "snap_a", {"key": "snap_a", "method": "GET"})
    _, _, renamed = merge_directories(src, dst, strategy="keep_both")
    assert renamed == 1
    assert (dst / "snap_a_merged.json").exists()
    assert _read(dst, "snap_a")["method"] == "GET"  # original untouched


def test_conflict_keep_both_key_field_updated(snap_dir):
    src, dst = snap_dir
    _write(src, "snap_a", {"key": "snap_a"})
    _write(dst, "snap_a", {"key": "snap_a"})
    merge_directories(src, dst, strategy="keep_both")
    assert _read(dst, "snap_a_merged")["key"] == "snap_a_merged"


def test_invalid_strategy_raises(snap_dir):
    src, dst = snap_dir
    _write(src, "snap_a", {"key": "snap_a"})
    _write(dst, "snap_a", {"key": "snap_a"})
    with pytest.raises(ValueError, match="Unknown conflict strategy"):
        merge_directories(src, dst, strategy="invalid")  # type: ignore[arg-type]
