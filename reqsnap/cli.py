"""CLI entry-point for reqsnap.

Commands
--------
list    – list recorded snapshots
show    – pretty-print a single snapshot
delete  – remove a snapshot file
diff    – compare two snapshots and display differences
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from reqsnap.storage import load_snapshot
from reqsnap.matcher import list_snapshots
from reqsnap.differ import diff_snapshots, is_identical


def cmd_list(args: argparse.Namespace) -> None:
    snap_dir = Path(args.snap_dir)
    snaps = list_snapshots(snap_dir)
    if not snaps:
        print("No snapshots found.")
        return
    for snap in snaps:
        print(snap.name)


def cmd_show(args: argparse.Namespace) -> None:
    snap_dir = Path(args.snap_dir)
    path = snap_dir / args.key
    if not path.exists():
        print(f"Snapshot not found: {args.key}", file=sys.stderr)
        sys.exit(1)
    data = load_snapshot(path)
    print(json.dumps(data, indent=2))


def cmd_delete(args: argparse.Namespace) -> None:
    snap_dir = Path(args.snap_dir)
    path = snap_dir / args.key
    if not path.exists():
        print(f"Snapshot not found: {args.key}", file=sys.stderr)
        sys.exit(1)
    path.unlink()
    print(f"Deleted {args.key}")


def cmd_diff(args: argparse.Namespace) -> None:
    """Compare two snapshots by key and print a JSON diff."""
    snap_dir = Path(args.snap_dir)
    path_a = snap_dir / args.key_a
    path_b = snap_dir / args.key_b

    for label, path in ((args.key_a, path_a), (args.key_b, path_b)):
        if not path.exists():
            print(f"Snapshot not found: {label}", file=sys.stderr)
            sys.exit(1)

    snap_a = load_snapshot(path_a)
    snap_b = load_snapshot(path_b)
    diff = diff_snapshots(snap_a, snap_b)

    if is_identical(diff):
        print("Snapshots are identical.")
    else:
        print(json.dumps(diff, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reqsnap",
        description="HTTP request recorder and replay tool.",
    )
    parser.add_argument(
        "--snap-dir",
        default=".reqsnap",
        help="Directory where snapshots are stored (default: .reqsnap)",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="List recorded snapshots")

    show_p = sub.add_parser("show", help="Show a snapshot")
    show_p.add_argument("key", help="Snapshot filename")

    del_p = sub.add_parser("delete", help="Delete a snapshot")
    del_p.add_argument("key", help="Snapshot filename")

    diff_p = sub.add_parser("diff", help="Diff two snapshots")
    diff_p.add_argument("key_a", help="First snapshot filename (baseline)")
    diff_p.add_argument("key_b", help="Second snapshot filename")

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    dispatch = {
        "list": cmd_list,
        "show": cmd_show,
        "delete": cmd_delete,
        "diff": cmd_diff,
    }
    if args.command not in dispatch:
        parser.print_help()
        sys.exit(1)
    dispatch[args.command](args)


if __name__ == "__main__":  # pragma: no cover
    main()
