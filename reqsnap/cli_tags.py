"""CLI sub-commands for snapshot tagging (cmd_tag_add, cmd_tag_remove, cmd_tag_list)."""
from __future__ import annotations

import argparse
from pathlib import Path

from reqsnap.tagger import add_tag, all_tags, filter_by_tag, get_tags, remove_tag


def cmd_tag_add(args: argparse.Namespace) -> None:
    """Add a tag to a snapshot."""
    snap_dir = Path(args.snap_dir)
    add_tag(snap_dir, args.key, args.tag)
    print(f"Tagged '{args.key}' with '{args.tag}'.")


def cmd_tag_remove(args: argparse.Namespace) -> None:
    """Remove a tag from a snapshot."""
    snap_dir = Path(args.snap_dir)
    remove_tag(snap_dir, args.key, args.tag)
    print(f"Removed tag '{args.tag}' from '{args.key}'.")


def cmd_tag_list(args: argparse.Namespace) -> None:
    """List tags — either for a specific snapshot key or all known tags."""
    snap_dir = Path(args.snap_dir)
    if args.key:
        tags = get_tags(snap_dir, args.key)
        if tags:
            for t in tags:
                print(t)
        else:
            print(f"No tags for '{args.key}'.")
    elif args.filter:
        keys = filter_by_tag(snap_dir, args.filter)
        if keys:
            for k in keys:
                print(k)
        else:
            print(f"No snapshots tagged '{args.filter}'.")
    else:
        tags = all_tags(snap_dir)
        if tags:
            for t in tags:
                print(t)
        else:
            print("No tags found.")


def register_tag_commands(subparsers) -> None:  # type: ignore[type-arg]
    """Attach tag sub-commands to an existing argparse subparsers group."""
    # tag add
    p_add = subparsers.add_parser("tag-add", help="Tag a snapshot")
    p_add.add_argument("key", help="Snapshot key")
    p_add.add_argument("tag", help="Tag label")
    p_add.add_argument("--snap-dir", default=".reqsnap")
    p_add.set_defaults(func=cmd_tag_add)

    # tag remove
    p_rm = subparsers.add_parser("tag-remove", help="Remove a tag from a snapshot")
    p_rm.add_argument("key", help="Snapshot key")
    p_rm.add_argument("tag", help="Tag label")
    p_rm.add_argument("--snap-dir", default=".reqsnap")
    p_rm.set_defaults(func=cmd_tag_remove)

    # tag list
    p_ls = subparsers.add_parser("tag-list", help="List tags")
    p_ls.add_argument("--key", default=None, help="Show tags for a specific snapshot")
    p_ls.add_argument("--filter", default=None, help="Filter snapshots by tag")
    p_ls.add_argument("--snap-dir", default=".reqsnap")
    p_ls.set_defaults(func=cmd_tag_list)
