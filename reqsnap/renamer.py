"""Rename (alias) snapshots by copying to a new key and removing the old one."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from reqsnap.storage import snapshot_path


def _snap_files(snap_dir: Path, key: str) -> list[Path]:
    """Return all files that belong to *key* (snapshot + any side-car files)."""
    base = snapshot_path(snap_dir, key)
    candidates = [base]
    # include tag / expiry side-cars that share the stem
    for sibling in snap_dir.iterdir():
        if sibling.stem == base.stem and sibling != base:
            candidates.append(sibling)
    return [p for p in candidates if p.exists()]


def rename_snapshot(snap_dir: Path, old_key: str, new_key: str) -> None:
    """Rename *old_key* to *new_key* inside *snap_dir*.

    Raises
    ------
    FileNotFoundError
        If the snapshot for *old_key* does not exist.
    FileExistsError
        If a snapshot for *new_key* already exists.
    """
    old_path = snapshot_path(snap_dir, old_key)
    new_path = snapshot_path(snap_dir, new_key)

    if not old_path.exists():
        raise FileNotFoundError(f"Snapshot not found: {old_key}")
    if new_path.exists():
        raise FileExistsError(f"Snapshot already exists: {new_key}")

    # Move the primary snapshot file.
    shutil.move(str(old_path), str(new_path))

    # Patch the stored key field so the snapshot stays self-consistent.
    data = json.loads(new_path.read_text(encoding="utf-8"))
    data["key"] = new_key
    new_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # Move any side-car files (tags, expiry …).
    old_stem = old_path.stem
    new_stem = new_path.stem
    for sibling in list(snap_dir.iterdir()):
        if sibling.stem == old_stem and sibling != old_path:
            dest = sibling.with_stem(new_stem) if hasattr(sibling, "with_stem") else (
                sibling.parent / (new_stem + sibling.suffix)
            )
            shutil.move(str(sibling), str(dest))


def list_keys(snap_dir: Path) -> list[str]:
    """Return the *key* field from every snapshot in *snap_dir*."""
    keys: list[str] = []
    for p in sorted(snap_dir.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if "key" in data:
                keys.append(data["key"])
        except (json.JSONDecodeError, OSError):
            continue
    return keys
