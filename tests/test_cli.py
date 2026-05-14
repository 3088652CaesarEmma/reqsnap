"""Tests for reqsnap CLI commands."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from reqsnap.cli import build_parser, cmd_list, cmd_show, cmd_delete
from reqsnap.storage import save_snapshot


SAMPLE_SNAPSHOT = {
    "request": {"method": "GET", "url": "https://example.com/api", "headers": {}, "body": ""},
    "response": {"status_code": 200, "headers": {}, "body": "{\"ok\": true}"},
}


@pytest.fixture()
def snap_dir(tmp_path: Path) -> Path:
    d = tmp_path / ".reqsnap"
    d.mkdir()
    return d


def _make_args(snap_dir: Path, command: str, **kwargs):
    parser = build_parser()
    base = ["--snap-dir", str(snap_dir), command]
    for k, v in kwargs.items():
        base += [v] if not k.startswith("--") else [k, v]
    return parser.parse_args(base)


class TestCmdList:
    def test_empty_directory(self, snap_dir: Path, capsys):
        args = _make_args(snap_dir, "list")
        rc = cmd_list(args)
        assert rc == 0
        assert "No snapshots found" in capsys.readouterr().out

    def test_lists_snapshots(self, snap_dir: Path, capsys):
        save_snapshot(snap_dir, "GET", "https://example.com/api", b"", SAMPLE_SNAPSHOT)
        args = _make_args(snap_dir, "list")
        rc = cmd_list(args)
        assert rc == 0
        out = capsys.readouterr().out
        assert "1 snapshot" in out
        assert "https://example.com/api" in out
        assert "HTTP 200" in out

    def test_missing_directory(self, tmp_path: Path, capsys):
        args = _make_args(tmp_path / "nonexistent", "list")
        rc = cmd_list(args)
        assert rc == 1
        assert "not found" in capsys.readouterr().err


class TestCmdShow:
    def test_show_existing(self, snap_dir: Path, capsys):
        save_snapshot(snap_dir, "GET", "https://example.com/api", b"", SAMPLE_SNAPSHOT)
        args = _make_args(snap_dir, "show", **{"0": "GET", "1": "https://example.com/api"})
        # Use positional args directly
        parser = build_parser()
        args = parser.parse_args(["--snap-dir", str(snap_dir), "show", "GET", "https://example.com/api"])
        rc = cmd_show(args)
        assert rc == 0
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["response"]["status_code"] == 200

    def test_show_missing(self, snap_dir: Path, capsys):
        parser = build_parser()
        args = parser.parse_args(["--snap-dir", str(snap_dir), "show", "GET", "https://missing.example.com"])
        rc = cmd_show(args)
        assert rc == 1
        assert "No snapshot found" in capsys.readouterr().err


class TestCmdDelete:
    def test_delete_existing(self, snap_dir: Path, capsys):
        save_snapshot(snap_dir, "GET", "https://example.com/api", b"", SAMPLE_SNAPSHOT)
        parser = build_parser()
        args = parser.parse_args(["--snap-dir", str(snap_dir), "delete", "GET", "https://example.com/api"])
        rc = cmd_delete(args)
        assert rc == 0
        assert "Deleted" in capsys.readouterr().out
        assert not any(snap_dir.glob("*.json"))

    def test_delete_missing(self, snap_dir: Path, capsys):
        parser = build_parser()
        args = parser.parse_args(["--snap-dir", str(snap_dir), "delete", "POST", "https://gone.example.com"])
        rc = cmd_delete(args)
        assert rc == 1
        assert "No snapshot found" in capsys.readouterr().err
