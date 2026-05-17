"""Snapshot persistence — save and load recorded HTTP responses."""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional


def _make_key(url: str, method: str, body: bytes = b"") -> str:
    """Return a deterministic hex key for a request triple."""
    raw = f"{method.upper()}:{url}".encode() + b":"
    if body:
        raw += body
    return hashlib.sha256(raw).hexdigest()


def snapshot_path(
    url: str,
    method: str,
    body: bytes = b"",
    snap_dir: str = "snapshots",
) -> Path:
    """Return the Path where a snapshot for this request would be stored."""
    key = _make_key(url, method, body)
    return Path(snap_dir) / f"{key}.json"


def save_snapshot(
    url: str,
    method: str,
    request_body: bytes,
    status_code: int,
    response_headers: Dict[str, str],
    response_body: str,
    snap_dir: str = "snapshots",
) -> Path:
    """Persist a response snapshot to disk and return its path."""
    path = snapshot_path(url, method, request_body, snap_dir=snap_dir)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload: Dict[str, Any] = {
        "url": url,
        "method": method.upper(),
        "status_code": status_code,
        "headers": dict(response_headers),
        "body": response_body,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_snapshot(
    url: str,
    method: str,
    body: bytes = b"",
    snap_dir: str = "snapshots",
) -> Optional[Dict[str, Any]]:
    """Load a snapshot from disk, or return None if it does not exist."""
    path = snapshot_path(url, method, body, snap_dir=snap_dir)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Snapshot file is corrupted or contains invalid JSON: {path}"
        ) from exc


def delete_snapshot(
    url: str,
    method: str,
    body: bytes = b"",
    snap_dir: str = "snapshots",
) -> bool:
    """Delete a snapshot from disk.

    Returns True if the snapshot existed and was deleted, False if it was
    not found.
    """
    path = snapshot_path(url, method, body, snap_dir=snap_dir)
    if not path.exists():
        return False
    path.unlink()
    return True
