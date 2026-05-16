"""reqsnap.cloner — duplicate an existing snapshot under a new key."""

from __future__ import annotations

import copy
from pathlib import Path

from reqsnap.storage import snapshot_path, save_snapshot, load_snapshot


def _snap_files(snap_dir: Path) -> list[Path]:
    """Return all .json snapshot files in *snap_dir*."""
    return sorted(snap_dir.glob("*.json"))


def list_keys(snap_dir: Path) -> list[str]:
    """Return the snapshot keys (stems) present in *snap_dir*."""
    return [p.stem for p in _snap_files(snap_dir)]


def clone_snapshot(
    snap_dir: Path,
    source_key: str,
    dest_key: str,
    *,
    overwrite: bool = False,
) -> Path:
    """Copy the snapshot identified by *source_key* to *dest_key*.

    Parameters
    ----------
    snap_dir:   Directory that holds the snapshot files.
    source_key: Key (file stem) of the snapshot to copy.
    dest_key:   Key (file stem) for the new snapshot.
    overwrite:  When *False* (default) raise ``FileExistsError`` if the
                destination already exists.

    Returns
    -------
    The :class:`~pathlib.Path` of the newly created snapshot file.
    """
    src_path = snapshot_path(snap_dir, source_key)
    if not src_path.exists():
        raise FileNotFoundError(f"Snapshot not found: {source_key!r}")

    dst_path = snapshot_path(snap_dir, dest_key)
    if dst_path.exists() and not overwrite:
        raise FileExistsError(
            f"Destination snapshot already exists: {dest_key!r}. "
            "Pass overwrite=True to replace it."
        )

    data = load_snapshot(snap_dir, source_key)
    cloned = copy.deepcopy(data)
    cloned["key"] = dest_key

    save_snapshot(snap_dir, dest_key, cloned)
    return dst_path
