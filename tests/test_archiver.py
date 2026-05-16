"""Tests for reqsnap.archiver."""

from __future__ import annotations

import json
import tarfile
from pathlib import Path

import pytest

from reqsnap.archiver import create_archive, restore_archive


@pytest.fixture()
def snap_dir(tmp_path: Path) -> Path:
    d = tmp_path / "snaps"
    d.mkdir()
    return d


def _write_snap(snap_dir: Path, name: str, data: dict) -> Path:
    p = snap_dir / f"{name}.json"
    p.write_text(json.dumps(data))
    return p


class TestCreateArchive:
    def test_creates_tar_gz_file(self, snap_dir: Path, tmp_path: Path) -> None:
        _write_snap(snap_dir, "snap1", {"method": "GET"})
        out = create_archive(snap_dir, dest_dir=tmp_path)
        assert out.suffix == ".gz"
        assert out.exists()

    def test_archive_contains_snapshots(self, snap_dir: Path, tmp_path: Path) -> None:
        _write_snap(snap_dir, "snap1", {"method": "GET"})
        _write_snap(snap_dir, "snap2", {"method": "POST"})
        out = create_archive(snap_dir, dest_dir=tmp_path)
        with tarfile.open(out, "r:gz") as tar:
            names = tar.getnames()
        assert "snap1.json" in names
        assert "snap2.json" in names

    def test_label_appears_in_filename(self, snap_dir: Path, tmp_path: Path) -> None:
        _write_snap(snap_dir, "snap1", {})
        out = create_archive(snap_dir, dest_dir=tmp_path, label="mytest")
        assert "mytest" in out.name

    def test_tag_filter_includes_only_tagged(self, snap_dir: Path, tmp_path: Path) -> None:
        _write_snap(snap_dir, "snap1", {"method": "GET"})
        _write_snap(snap_dir, "snap2", {"method": "POST"})
        tags_file = snap_dir / "_tags.json"
        tags_file.write_text(json.dumps({"snap1": ["smoke"], "snap2": ["slow"]}))
        out = create_archive(snap_dir, dest_dir=tmp_path, tags=["smoke"])
        with tarfile.open(out, "r:gz") as tar:
            names = tar.getnames()
        assert "snap1.json" in names
        assert "snap2.json" not in names

    def test_metadata_files_included(self, snap_dir: Path, tmp_path: Path) -> None:
        _write_snap(snap_dir, "snap1", {})
        (snap_dir / "_tags.json").write_text(json.dumps({}))
        (snap_dir / "_expiry.json").write_text(json.dumps({}))
        out = create_archive(snap_dir, dest_dir=tmp_path)
        with tarfile.open(out, "r:gz") as tar:
            names = tar.getnames()
        assert "_tags.json" in names
        assert "_expiry.json" in names


class TestRestoreArchive:
    def _make_archive(self, snap_dir: Path, tmp_path: Path) -> Path:
        _write_snap(snap_dir, "snap1", {"method": "GET"})
        return create_archive(snap_dir, dest_dir=tmp_path)

    def test_restores_files(self, snap_dir: Path, tmp_path: Path) -> None:
        archive = self._make_archive(snap_dir, tmp_path)
        dest = tmp_path / "restored"
        written = restore_archive(archive, dest)
        assert "snap1.json" in written
        assert (dest / "snap1.json").exists()

    def test_skips_existing_without_overwrite(self, snap_dir: Path, tmp_path: Path) -> None:
        archive = self._make_archive(snap_dir, tmp_path)
        dest = tmp_path / "restored"
        dest.mkdir()
        existing = dest / "snap1.json"
        existing.write_text("original")
        written = restore_archive(archive, dest, overwrite=False)
        assert "snap1.json" not in written
        assert existing.read_text() == "original"

    def test_overwrites_when_flag_set(self, snap_dir: Path, tmp_path: Path) -> None:
        archive = self._make_archive(snap_dir, tmp_path)
        dest = tmp_path / "restored"
        dest.mkdir()
        existing = dest / "snap1.json"
        existing.write_text("old")
        restore_archive(archive, dest, overwrite=True)
        assert existing.read_text() != "old"
