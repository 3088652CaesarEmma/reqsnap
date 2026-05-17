"""Tests for reqsnap.cli_grouper."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from reqsnap.cli_grouper import cmd_group, register_grouper_commands


@pytest.fixture()
def snap_dir(tmp_path: Path) -> Path:
    return tmp_path


def _args(snap_dir: Path, by: str = "host") -> argparse.Namespace:
    return argparse.Namespace(snap_dir=str(snap_dir), by=by)


def _write(snap_dir: Path, key: str, snap: dict) -> None:
    snap.setdefault("key", key)
    (snap_dir / f"{key}.json").write_text(json.dumps(snap))


def _base(method="GET", url="https://api.example.com/", status=200):
    return {
        "method": method,
        "url": url,
        "response": {"status_code": status, "headers": {}, "body": None},
    }


def test_cmd_group_prints_output(snap_dir, capsys):
    _write(snap_dir, "snap1", _base())
    cmd_group(_args(snap_dir, by="host"))
    out = capsys.readouterr().out
    assert "api.example.com" in out


def test_cmd_group_missing_dir_prints_message(tmp_path, capsys):
    missing = tmp_path / "no_such_dir"
    cmd_group(_args(missing))
    out = capsys.readouterr().out
    assert "not found" in out.lower()


def test_cmd_group_invalid_by_prints_error(snap_dir, capsys):
    cmd_group(_args(snap_dir, by="invalid"))
    out = capsys.readouterr().out
    assert "Error" in out


def test_cmd_group_empty_dir_prints_no_snapshots(snap_dir, capsys):
    cmd_group(_args(snap_dir))
    out = capsys.readouterr().out
    assert "no snapshots" in out


def test_register_grouper_commands_adds_group_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_grouper_commands(sub, "/tmp/snaps")
    ns = parser.parse_args(["group", "--by", "method"])
    assert ns.by == "method"


def test_register_grouper_commands_default_by_is_host():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_grouper_commands(sub, "/tmp/snaps")
    ns = parser.parse_args(["group"])
    assert ns.by == "host"
