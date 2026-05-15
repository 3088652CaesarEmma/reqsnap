"""Summarize collections of snapshots for reporting and display."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from reqsnap.storage import load_snapshot
from reqsnap.matcher import list_snapshots


def _method_counts(snapshots: List[dict]) -> Dict[str, int]:
    """Return a mapping of HTTP method -> count."""
    counts: Dict[str, int] = {}
    for snap in snapshots:
        method = snap.get("request", {}).get("method", "UNKNOWN").upper()
        counts[method] = counts.get(method, 0) + 1
    return counts


def _status_counts(snapshots: List[dict]) -> Dict[int, int]:
    """Return a mapping of HTTP status code -> count."""
    counts: Dict[int, int] = {}
    for snap in snapshots:
        status = snap.get("response", {}).get("status_code", 0)
        counts[status] = counts.get(status, 0) + 1
    return counts


def _unique_hosts(snapshots: List[dict]) -> List[str]:
    """Return sorted list of unique hosts found across snapshots."""
    hosts = set()
    for snap in snapshots:
        url: str = snap.get("request", {}).get("url", "")
        if "://" in url:
            host = url.split("://", 1)[1].split("/")[0].split("?")[0]
            hosts.add(host)
    return sorted(hosts)


def summarize_directory(snap_dir: Path) -> dict:
    """Return a summary dict for all snapshots in *snap_dir*."""
    keys = list_snapshots(snap_dir)
    snapshots: List[dict] = []
    for key in keys:
        snap = load_snapshot(snap_dir, key)
        if snap is not None:
            snapshots.append(snap)

    return {
        "total": len(snapshots),
        "methods": _method_counts(snapshots),
        "status_codes": _status_counts(snapshots),
        "hosts": _unique_hosts(snapshots),
    }


def format_summary(summary: dict) -> str:
    """Return a human-readable string for *summary*."""
    lines = [
        f"Total snapshots : {summary['total']}",
        "Methods         : "
        + ", ".join(f"{m}={c}" for m, c in sorted(summary["methods"].items())),
        "Status codes    : "
        + ", ".join(f"{s}={c}" for s, c in sorted(summary["status_codes"].items())),
        "Hosts           : " + ", ".join(summary["hosts"]) if summary["hosts"] else "Hosts           : (none)",
    ]
    return "\n".join(lines)
