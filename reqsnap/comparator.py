"""Snapshot comparator: compare two snapshots side-by-side and produce a structured report."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from reqsnap.storage import load_snapshot


@dataclass
class CompareReport:
    key_a: str
    key_b: str
    matching_fields: list[str] = field(default_factory=list)
    differing_fields: dict[str, dict[str, Any]] = field(default_factory=dict)
    only_in_a: list[str] = field(default_factory=list)
    only_in_b: list[str] = field(default_factory=list)

    @property
    def is_identical(self) -> bool:
        return (
            not self.differing_fields
            and not self.only_in_a
            and not self.only_in_b
        )


_COMPARE_FIELDS = [
    "method",
    "url",
    "status_code",
    "request_body",
    "response_body",
]


def _flat_headers(snap: dict, role: str) -> dict[str, str]:
    """Return lowercased header dict for 'request' or 'response'."""
    headers = snap.get(f"{role}_headers") or {}
    return {k.lower(): v for k, v in headers.items()}


def compare_snapshots(snap_dir: Path, key_a: str, key_b: str) -> CompareReport:
    """Load two snapshots by key and compare their fields."""
    snap_a = load_snapshot(snap_dir, key_a)
    snap_b = load_snapshot(snap_dir, key_b)

    if snap_a is None:
        raise FileNotFoundError(f"Snapshot not found: {key_a}")
    if snap_b is None:
        raise FileNotFoundError(f"Snapshot not found: {key_b}")

    report = CompareReport(key_a=key_a, key_b=key_b)

    for f in _COMPARE_FIELDS:
        val_a = snap_a.get(f)
        val_b = snap_b.get(f)
        if val_a == val_b:
            report.matching_fields.append(f)
        else:
            report.differing_fields[f] = {"a": val_a, "b": val_b}

    for role in ("request", "response"):
        hdrs_a = _flat_headers(snap_a, role)
        hdrs_b = _flat_headers(snap_b, role)
        all_keys = set(hdrs_a) | set(hdrs_b)
        for k in sorted(all_keys):
            field_name = f"{role}_header:{k}"
            if k not in hdrs_a:
                report.only_in_b.append(field_name)
            elif k not in hdrs_b:
                report.only_in_a.append(field_name)
            elif hdrs_a[k] == hdrs_b[k]:
                report.matching_fields.append(field_name)
            else:
                report.differing_fields[field_name] = {"a": hdrs_a[k], "b": hdrs_b[k]}

    return report
