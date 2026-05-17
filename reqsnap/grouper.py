"""Group snapshots by a chosen dimension (host, method, status)."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse


def _snap_files(snap_dir: Path):
    return sorted(snap_dir.glob("*.json"))


def _load(path: Path) -> Optional[dict]:
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def _host(snap: dict) -> str:
    url = snap.get("url", "")
    parsed = urlparse(url)
    return parsed.netloc or "unknown"


def _method(snap: dict) -> str:
    return snap.get("method", "UNKNOWN").upper()


def _status(snap: dict) -> str:
    code = snap.get("response", {}).get("status_code")
    if code is None:
        return "unknown"
    return str(code)


_DIMENSIONS = {
    "host": _host,
    "method": _method,
    "status": _status,
}


def group_snapshots(
    snap_dir: Path, by: str = "host"
) -> Dict[str, List[str]]:
    """Return a mapping of dimension-value -> list of snapshot keys.

    Args:
        snap_dir: Directory containing snapshot JSON files.
        by: Grouping dimension — one of 'host', 'method', 'status'.

    Returns:
        Dict mapping group label to list of snapshot key strings.

    Raises:
        ValueError: If *by* is not a recognised dimension.
    """
    if by not in _DIMENSIONS:
        raise ValueError(
            f"Unknown dimension {by!r}. Choose from: {list(_DIMENSIONS)}"
        )

    extractor = _DIMENSIONS[by]
    groups: Dict[str, List[str]] = defaultdict(list)

    for path in _snap_files(snap_dir):
        snap = _load(path)
        if snap is None:
            continue
        label = extractor(snap)
        key = snap.get("key", path.stem)
        groups[label].append(key)

    return dict(groups)


def format_groups(groups: Dict[str, List[str]]) -> str:
    """Return a human-readable string representation of groups."""
    if not groups:
        return "(no snapshots)"
    lines: List[str] = []
    for label in sorted(groups):
        keys = groups[label]
        lines.append(f"{label} ({len(keys)}):")
        for k in keys:
            lines.append(f"  - {k}")
    return "\n".join(lines)
