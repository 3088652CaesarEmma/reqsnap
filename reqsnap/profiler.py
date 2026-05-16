"""Snapshot profiling: compute timing and size statistics for recorded snapshots."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from reqsnap.storage import load_snapshot
from reqsnap.matcher import list_snapshots


@dataclass
class SnapshotProfile:
    key: str
    method: str
    url: str
    status_code: int
    request_body_bytes: int
    response_body_bytes: int
    response_time_ms: Optional[float]

    @property
    def total_bytes(self) -> int:
        return self.request_body_bytes + self.response_body_bytes


def _body_size(body) -> int:
    """Return byte length of a body value (str, bytes, dict, or None)."""
    if body is None:
        return 0
    if isinstance(body, bytes):
        return len(body)
    if isinstance(body, dict):
        return len(json.dumps(body).encode())
    return len(str(body).encode())


def profile_snapshot(snap_dir: Path, key: str) -> Optional[SnapshotProfile]:
    """Load a single snapshot and return its profile, or None if not found."""
    snap = load_snapshot(snap_dir, key)
    if snap is None:
        return None

    req = snap.get("request", {})
    resp = snap.get("response", {})

    return SnapshotProfile(
        key=key,
        method=req.get("method", "UNKNOWN"),
        url=req.get("url", ""),
        status_code=resp.get("status_code", 0),
        request_body_bytes=_body_size(req.get("body")),
        response_body_bytes=_body_size(resp.get("body")),
        response_time_ms=resp.get("elapsed_ms"),
    )


def profile_directory(snap_dir: Path) -> List[SnapshotProfile]:
    """Return profiles for all snapshots found in *snap_dir*."""
    profiles = []
    for key in list_snapshots(snap_dir):
        p = profile_snapshot(snap_dir, key)
        if p is not None:
            profiles.append(p)
    return profiles


def format_profile_report(profiles: List[SnapshotProfile]) -> str:
    """Render a human-readable table of snapshot profiles."""
    if not profiles:
        return "No snapshots found."

    lines = [
        f"{'KEY':<36}  {'METHOD':<7}  {'STATUS':<6}  {'REQ B':>7}  {'RESP B':>7}  {'TIME ms':>9}",
        "-" * 82,
    ]
    for p in profiles:
        time_str = f"{p.response_time_ms:.1f}" if p.response_time_ms is not None else "n/a"
        lines.append(
            f"{p.key:<36}  {p.method:<7}  {p.status_code:<6}  "
            f"{p.request_body_bytes:>7}  {p.response_body_bytes:>7}  {time_str:>9}"
        )
    return "\n".join(lines)
