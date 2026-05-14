"""Request matching utilities for finding snapshots that match incoming requests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .storage import _make_key, load_snapshot, snapshot_path


def _normalize_headers(headers: dict) -> dict:
    """Normalize headers to lowercase keys for comparison."""
    return {k.lower(): v for k, v in (headers or {}).items()}


def _bodies_match(recorded_body: Optional[str], request_body: Optional[str]) -> bool:
    """Compare two request bodies, attempting JSON-aware comparison."""
    if recorded_body == request_body:
        return True
    if not recorded_body and not request_body:
        return True
    if not recorded_body or not request_body:
        return False
    try:
        return json.loads(recorded_body) == json.loads(request_body)
    except (json.JSONDecodeError, TypeError):
        return False


def find_match(
    snap_dir: Path,
    method: str,
    url: str,
    body: Optional[str] = None,
) -> Optional[dict]:
    """Find a snapshot that matches the given request parameters.

    First attempts an exact key match, then falls back to scanning all
    snapshots in the directory for a body-normalized match.

    Args:
        snap_dir: Directory containing snapshot files.
        method: HTTP method (e.g. 'GET', 'POST').
        url: Full request URL.
        body: Optional request body string.

    Returns:
        The matching snapshot dict, or None if no match is found.
    """
    exact_path = snapshot_path(snap_dir, method, url, body)
    if exact_path.exists():
        return load_snapshot(exact_path)

    # Fallback: scan all snapshots for a normalized body match
    for snap_file in snap_dir.glob("*.json"):
        snapshot = load_snapshot(snap_file)
        req = snapshot.get("request", {})
        if req.get("method", "").upper() != method.upper():
            continue
        if req.get("url") != url:
            continue
        if _bodies_match(req.get("body"), body):
            return snapshot

    return None


def list_snapshots(snap_dir: Path) -> list[dict]:
    """Return a list of all snapshots in the directory, sorted by URL then method."""
    snapshots = []
    for snap_file in sorted(snap_dir.glob("*.json")):
        snapshot = load_snapshot(snap_file)
        snapshots.append(snapshot)
    snapshots.sort(key=lambda s: (s.get("request", {}).get("url", ""), s.get("request", {}).get("method", "")))
    return snapshots
