"""Storage module for recording and loading HTTP snapshots."""

import json
import os
import hashlib
from datetime import datetime
from typing import Optional

DEFAULT_SNAPSHOT_DIR = ".reqsnap"


def _make_key(method: str, url: str, body: Optional[bytes] = None) -> str:
    """Generate a deterministic filename key for a request."""
    raw = f"{method.upper()}:{url}"
    if body:
        raw += ":" + hashlib.md5(body).hexdigest()
    return hashlib.sha1(raw.encode()).hexdigest()[:12]


def snapshot_path(method: str, url: str, body: Optional[bytes] = None,
                  snapshot_dir: str = DEFAULT_SNAPSHOT_DIR) -> str:
    """Return the file path for a given request snapshot."""
    key = _make_key(method, url, body)
    os.makedirs(snapshot_dir, exist_ok=True)
    return os.path.join(snapshot_dir, f"{key}.json")


def save_snapshot(method: str, url: str, response: dict,
                  body: Optional[bytes] = None,
                  snapshot_dir: str = DEFAULT_SNAPSHOT_DIR) -> str:
    """Persist a response snapshot to disk. Returns the file path."""
    path = snapshot_path(method, url, body, snapshot_dir)
    record = {
        "method": method.upper(),
        "url": url,
        "recorded_at": datetime.utcnow().isoformat() + "Z",
        "response": response,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)
    return path


def load_snapshot(method: str, url: str, body: Optional[bytes] = None,
                  snapshot_dir: str = DEFAULT_SNAPSHOT_DIR) -> Optional[dict]:
    """Load a previously recorded snapshot. Returns None if not found."""
    path = snapshot_path(method, url, body, snapshot_dir)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
