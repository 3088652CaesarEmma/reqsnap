"""Tests for reqsnap.cli_scheduler."""

from __future__ import annotations

import json
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from reqsnap.cli_scheduler import (
    cmd_expire_remove,
    cmd_expire_set,
    cmd_expire_show,
    cmd_purge,
)
from reqsnap.scheduler import get_expiry, set_expiry


@pytest.fixture()
def snap_dir(tmp_path: Path) -> Path:
    return tmp_path


def _args(snap_dir: Path, **kwargs) -> SimpleNamespace:
    return SimpleNamespace(snap_dir=str(snap_dir), **kwargs)


def test_cmd_expire_set_stores_expiry(snap_dir, capsys):
    cmd_expire_set(_args(snap_dir, key="k1", ttl=120))
    expiry = get_expiry(snap_dir, "k1")
    assert expiry is not None
    assert expiry > time.time()


def test_cmd_expire_set_prints_confirmation(snap_dir, capsys):
    cmd_expire_set(_args(snap_dir, key="k1", ttl=60))
    out = capsys.readouterr().out
    assert "k1" in out
    assert "60" in out


def test_cmd_expire_show_no_expiry(snap_dir, capsys):
    cmd_expire_show(_args(snap_dir, key="ghost"))
    out = capsys.readouterr().out
    assert "no expiry" in out


def test_cmd_expire_show_future_expiry(snap_dir, capsys):
    set_expiry(snap_dir, "alive", ttl_seconds=3600)
    cmd_expire_show(_args(snap_dir, key="alive"))
    out = capsys.readouterr().out
    assert "expires in" in out


def test_cmd_expire_show_past_expiry(snap_dir, capsys):
    set_expiry(snap_dir, "dead", ttl_seconds=-10)
    cmd_expire_show(_args(snap_dir, key="dead"))
    out = capsys.readouterr().out
    assert "EXPIRED" in out


def test_cmd_expire_remove_clears_entry(snap_dir, capsys):
    set_expiry(snap_dir, "todel", ttl_seconds=60)
    cmd_expire_remove(_args(snap_dir, key="todel"))
    assert get_expiry(snap_dir, "todel") is None


def test_cmd_expire_remove_prints_confirmation(snap_dir, capsys):
    set_expiry(snap_dir, "todel", ttl_seconds=60)
    cmd_expire_remove(_args(snap_dir, key="todel"))
    out = capsys.readouterr().out
    assert "todel" in out


def test_cmd_purge_removes_expired_file(snap_dir, capsys):
    key = "expiredsnap"
    snap_file = snap_dir / f"{key}.json"
    snap_file.write_text(json.dumps({"method": "GET"}))
    set_expiry(snap_dir, key, ttl_seconds=-1)

    cmd_purge(_args(snap_dir))

    assert not snap_file.exists()
    out = capsys.readouterr().out
    assert key in out


def test_cmd_purge_nothing_to_purge(snap_dir, capsys):
    cmd_purge(_args(snap_dir))
    out = capsys.readouterr().out
    assert "No expired" in out
