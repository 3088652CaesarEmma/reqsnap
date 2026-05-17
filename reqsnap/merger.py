"""Merge two snapshot directories, with configurable conflict resolution."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal, List, Tuple

ConflictStrategy = Literal["keep_source", "keep_dest", "keep_both"]


def _snap_files(directory: Path) -> List[Path]:
    return sorted(directory.glob("*.json"))


def _load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _write(path: Path, data: dict) -> None:
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def merge_directories(
    source: Path,
    dest: Path,
    strategy: ConflictStrategy = "keep_dest",
) -> Tuple[int, int, int]:
    """Merge snapshots from *source* into *dest*.

    Returns a tuple of (copied, skipped, renamed) counts.
    """
    dest.mkdir(parents=True, exist_ok=True)
    copied = skipped = renamed = 0

    for src_file in _snap_files(source):
        dst_file = dest / src_file.name

        if not dst_file.exists():
            _write(dst_file, _load(src_file))
            copied += 1
            continue

        # Conflict — apply strategy
        if strategy == "keep_dest":
            skipped += 1
        elif strategy == "keep_source":
            _write(dst_file, _load(src_file))
            copied += 1
        elif strategy == "keep_both":
            stem = src_file.stem
            candidate = dest / f"{stem}_merged.json"
            counter = 1
            while candidate.exists():
                candidate = dest / f"{stem}_merged_{counter}.json"
                counter += 1
            data = _load(src_file)
            data["key"] = candidate.stem
            _write(candidate, data)
            renamed += 1
        else:
            raise ValueError(f"Unknown conflict strategy: {strategy!r}")

    return copied, skipped, renamed


def list_conflicts(source: Path, dest: Path) -> List[str]:
    """Return the stems of snapshots that exist in both directories."""
    source_stems = {f.stem for f in _snap_files(source)}
    dest_stems = {f.stem for f in _snap_files(dest)}
    return sorted(source_stems & dest_stems)
