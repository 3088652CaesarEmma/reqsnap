"""Tests for reqsnap.scheduler."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from reqsnap.scheduler import (
    get_expiry,
    is_expired,
    purge_expired,
    remove_expiry,
    set_expiry,
)


@pytest.fixture()
def snap_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_set_and_get_expiry(snap_dir):
    set_expiry(snap_dir, "abc123", ttl_seconds=60)
    expiry = get_expiry(snap_dir, "abc123")
    assert expiry is not None
    assert expiry > time.time()
    assert expiry <= time.time() + 61


def test_get_expiry_missing_key_returns_none(snap_dir):
    assert get_expiry(snap_dir, "no-such-key") is None


def test_is_expired_false_for_future_ttl(snap_dir):
    set_expiry(snap_dir, "future", ttl_seconds=3600)
    assert is_expired(snap_dir, "future") is False


def test_is_expired_true_for_past_ttl(snap_dir):
    set_expiry(snap_dir, "past", ttl_seconds=-1)
    assert is_expired(snap_dir, "past") is True


def test_is_expired_false_when_no_expiry_set(snap_dir):
    assert is_expired(snap_dir, "unknown") is False


def test_remove_expiry_clears_entry(snap_dir):
    set_expiry(snap_dir, "to_remove", ttl_seconds=60)
    remove_expiry(snap_dir, "to_remove")
    assert get_expiry(snap_dir, "to_remove") is None


def test_remove_expiry_nonexistent_is_safe(snap_dir):
    remove_expiry(snap_dir, "ghost")  # should not raise


def test_purge_expired_deletes_snapshot_file(snap_dir):
    key = "deadkey"
    snap_file = snap_dir / f"{key}.json"
    snap_file.write_text(json.dumps({"method": "GET"}))
    set_expiry(snap_dir, key, ttl_seconds=-1)

    purged = purge_expired(snap_dir)

    assert key in purged
    assert not snap_file.exists()


def test_purge_expired_leaves_valid_snapshots(snap_dir):
    valid_key = "validkey"
    snap_file = snap_dir / f"{valid_key}.json"
    snap_file.write_text(json.dumps({"method": "GET"}))
    set_expiry(snap_dir, valid_key, ttl_seconds=3600)

    purged = purge_expired(snap_dir)

    assert valid_key not in purged
    assert snap_file.exists()


def test_purge_expired_returns_empty_when_nothing_expired(snap_dir):
    set_expiry(snap_dir, "alive", ttl_seconds=3600)
    assert purge_expired(snap_dir) == []


def test_purge_expired_removes_expiry_entry(snap_dir):
    key = "expiredkey"
    set_expiry(snap_dir, key, ttl_seconds=-1)
    purge_expired(snap_dir)
    assert get_expiry(snap_dir, key) is None
