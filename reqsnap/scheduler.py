"""Snapshot expiry and TTL-based scheduling for reqsnap."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import List, Optional

_EXPIRY_FILE = ".expiry.json"


def _expiry_path(snap_dir: Path) -> Path:
    return snap_dir / _EXPIRY_FILE


def _load_expiry_map(snap_dir: Path) -> dict:
    path = _expiry_path(snap_dir)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_expiry_map(snap_dir: Path, data: dict) -> None:
    _expiry_path(snap_dir).write_text(json.dumps(data, indent=2))


def set_expiry(snap_dir: Path, key: str, ttl_seconds: int) -> None:
    """Set a TTL (in seconds from now) for a snapshot key."""
    data = _load_expiry_map(snap_dir)
    data[key] = time.time() + ttl_seconds
    _save_expiry_map(snap_dir, data)


def get_expiry(snap_dir: Path, key: str) -> Optional[float]:
    """Return the expiry timestamp for a key, or None if not set."""
    return _load_expiry_map(snap_dir).get(key)


def is_expired(snap_dir: Path, key: str) -> bool:
    """Return True if the snapshot key has passed its TTL."""
    expiry = get_expiry(snap_dir, key)
    if expiry is None:
        return False
    return time.time() > expiry


def remove_expiry(snap_dir: Path, key: str) -> None:
    """Remove the TTL entry for a key."""
    data = _load_expiry_map(snap_dir)
    data.pop(key, None)
    _save_expiry_map(snap_dir, data)


def purge_expired(snap_dir: Path) -> List[str]:
    """Delete snapshot files and expiry entries for all expired keys.

    Returns the list of keys that were purged.
    """
    data = _load_expiry_map(snap_dir)
    now = time.time()
    purged: List[str] = []

    for key, expiry in list(data.items()):
        if now > expiry:
            snap_file = snap_dir / f"{key}.json"
            if snap_file.exists():
                snap_file.unlink()
            del data[key]
            purged.append(key)

    _save_expiry_map(snap_dir, data)
    return purged
