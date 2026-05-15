"""Tag and filter snapshots with arbitrary labels."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional

TAGS_FILENAME = ".tags.json"


def _tags_path(snap_dir: Path) -> Path:
    return snap_dir / TAGS_FILENAME


def _load_tag_map(snap_dir: Path) -> Dict[str, List[str]]:
    """Return mapping of snapshot key -> list of tags."""
    p = _tags_path(snap_dir)
    if not p.exists():
        return {}
    with p.open() as fh:
        return json.load(fh)


def _save_tag_map(snap_dir: Path, tag_map: Dict[str, List[str]]) -> None:
    _tags_path(snap_dir).write_text(json.dumps(tag_map, indent=2))


def add_tag(snap_dir: Path, key: str, tag: str) -> None:
    """Add *tag* to the snapshot identified by *key*."""
    tag_map = _load_tag_map(snap_dir)
    tags = tag_map.setdefault(key, [])
    if tag not in tags:
        tags.append(tag)
    _save_tag_map(snap_dir, tag_map)


def remove_tag(snap_dir: Path, key: str, tag: str) -> None:
    """Remove *tag* from the snapshot identified by *key* (no-op if absent)."""
    tag_map = _load_tag_map(snap_dir)
    tags = tag_map.get(key, [])
    tag_map[key] = [t for t in tags if t != tag]
    _save_tag_map(snap_dir, tag_map)


def get_tags(snap_dir: Path, key: str) -> List[str]:
    """Return all tags for *key*, or an empty list."""
    return _load_tag_map(snap_dir).get(key, [])


def filter_by_tag(snap_dir: Path, tag: str) -> List[str]:
    """Return all snapshot keys that carry *tag*."""
    return [
        key
        for key, tags in _load_tag_map(snap_dir).items()
        if tag in tags
    ]


def all_tags(snap_dir: Path) -> List[str]:
    """Return a sorted, deduplicated list of every tag used in *snap_dir*."""
    seen: set = set()
    for tags in _load_tag_map(snap_dir).values():
        seen.update(tags)
    return sorted(seen)
