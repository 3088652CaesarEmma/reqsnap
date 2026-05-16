"""Archive and restore snapshot collections as compressed tarballs."""

from __future__ import annotations

import json
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def _archive_name(label: str | None = None) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = f"_{label}" if label else ""
    return f"reqsnap_archive{suffix}_{ts}.tar.gz"


def create_archive(
    snap_dir: Path,
    dest_dir: Path | None = None,
    label: str | None = None,
    tags: list[str] | None = None,
) -> Path:
    """Pack all (or tag-filtered) snapshots into a .tar.gz archive.

    Args:
        snap_dir: Directory containing snapshot JSON files.
        dest_dir: Where to write the archive (defaults to snap_dir).
        label: Optional human-readable label embedded in the filename.
        tags: If given, only include snapshots whose key appears in the
              tags map with at least one of the requested tags.

    Returns:
        Path to the created archive file.
    """
    dest_dir = dest_dir or snap_dir
    dest_dir.mkdir(parents=True, exist_ok=True)

    snapshots = sorted(snap_dir.glob("*.json"))

    if tags:
        tags_file = snap_dir / "_tags.json"
        tag_map: dict[str, list[str]] = {}
        if tags_file.exists():
            tag_map = json.loads(tags_file.read_text())
        requested = set(tags)
        snapshots = [
            p for p in snapshots
            if requested.intersection(tag_map.get(p.stem, []))
        ]

    archive_path = dest_dir / _archive_name(label)
    with tarfile.open(archive_path, "w:gz") as tar:
        for snap in snapshots:
            tar.add(snap, arcname=snap.name)
        # Include metadata side-files if present
        for meta in ("_tags.json", "_expiry.json"):
            meta_path = snap_dir / meta
            if meta_path.exists():
                tar.add(meta_path, arcname=meta)

    return archive_path


def restore_archive(
    archive_path: Path,
    snap_dir: Path,
    overwrite: bool = False,
) -> list[str]:
    """Extract snapshots from an archive into snap_dir.

    Args:
        archive_path: Path to the .tar.gz archive.
        snap_dir: Destination snapshot directory.
        overwrite: If False, skip files that already exist.

    Returns:
        List of filenames that were actually written.
    """
    snap_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    with tarfile.open(archive_path, "r:gz") as tar:
        for member in tar.getmembers():
            dest = snap_dir / member.name
            if dest.exists() and not overwrite:
                continue
            with tar.extractfile(member) as src, open(dest, "wb") as dst:  # type: ignore[union-attr]
                dst.write(src.read())
            written.append(member.name)

    return written
