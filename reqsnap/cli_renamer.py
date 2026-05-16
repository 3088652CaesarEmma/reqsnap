"""CLI sub-commands for renaming snapshots."""

from __future__ import annotations

import argparse
from pathlib import Path

from reqsnap.renamer import list_keys, rename_snapshot


def cmd_rename(args: argparse.Namespace) -> None:
    """Rename a snapshot from *old_key* to *new_key*."""
    snap_dir = Path(args.snap_dir)
    try:
        rename_snapshot(snap_dir, args.old_key, args.new_key)
        print(f"Renamed '{args.old_key}' → '{args.new_key}'")
    except FileNotFoundError as exc:
        print(f"Error: {exc}")
        raise SystemExit(1)
    except FileExistsError as exc:
        print(f"Error: {exc}")
        raise SystemExit(1)


def cmd_rename_list(args: argparse.Namespace) -> None:
    """List all snapshot keys in the snap directory."""
    snap_dir = Path(args.snap_dir)
    keys = list_keys(snap_dir)
    if not keys:
        print("No snapshots found.")
        return
    for key in keys:
        print(key)


def register_renamer_commands(
    subparsers: argparse._SubParsersAction,  # type: ignore[type-arg]
    snap_dir: str,
) -> None:
    """Attach *rename* and *rename-list* sub-commands to *subparsers*."""
    # rename
    p_rename = subparsers.add_parser("rename", help="Rename a snapshot key")
    p_rename.add_argument("old_key", help="Existing snapshot key")
    p_rename.add_argument("new_key", help="New snapshot key")
    p_rename.set_defaults(func=cmd_rename, snap_dir=snap_dir)

    # rename-list
    p_list = subparsers.add_parser(
        "rename-list", help="List all snapshot keys"
    )
    p_list.set_defaults(func=cmd_rename_list, snap_dir=snap_dir)
