"""Command-line interface for reqsnap."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from reqsnap.matcher import list_snapshots
from reqsnap.storage import load_snapshot, snapshot_path
from reqsnap.differ import diff_snapshots
from reqsnap.inspector import summarise_snapshot, validate_snapshot


def cmd_list(args: argparse.Namespace) -> None:
    snap_dir = Path(args.snap_dir)
    snaps = list_snapshots(snap_dir)
    if not snaps:
        print("No snapshots found.")
        return
    for p in snaps:
        print(p.name)


def cmd_show(args: argparse.Namespace) -> None:
    path = Path(args.snap_dir) / args.name
    if not path.exists():
        print(f"Snapshot not found: {args.name}", file=sys.stderr)
        sys.exit(1)
    snap = load_snapshot(path)
    print(json.dumps(snap, indent=2))


def cmd_delete(args: argparse.Namespace) -> None:
    path = Path(args.snap_dir) / args.name
    if not path.exists():
        print(f"Snapshot not found: {args.name}", file=sys.stderr)
        sys.exit(1)
    path.unlink()
    print(f"Deleted {args.name}")


def cmd_diff(args: argparse.Namespace) -> None:
    snap_dir = Path(args.snap_dir)
    a = load_snapshot(snap_dir / args.a)
    b = load_snapshot(snap_dir / args.b)
    result = diff_snapshots(a, b)
    if not result:
        print("Snapshots are identical.")
    else:
        print(json.dumps(result, indent=2))


def cmd_inspect(args: argparse.Namespace) -> None:
    """Summarise and optionally validate one or all snapshots."""
    snap_dir = Path(args.snap_dir)

    if args.name:
        paths = [snap_dir / args.name]
    else:
        paths = list_snapshots(snap_dir)

    if not paths:
        print("No snapshots found.")
        return

    for p in paths:
        summary = summarise_snapshot(p)
        print(
            f"{summary['file']}  "
            f"{summary['method']} {summary['url']}  "
            f"HTTP {summary['status']}  "
            f"{summary['response_body_bytes'] or 0}B"
        )
        if args.validate:
            warnings = validate_snapshot(p)
            if warnings:
                for w in warnings:
                    print(f"  ⚠  {w}")
            else:
                print("  ✓ valid")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="reqsnap", description="HTTP snapshot tool")
    parser.add_argument("--snap-dir", default=".reqsnap", help="Snapshot directory")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="List all snapshots")

    show_p = sub.add_parser("show", help="Print a snapshot as JSON")
    show_p.add_argument("name")

    del_p = sub.add_parser("delete", help="Delete a snapshot")
    del_p.add_argument("name")

    diff_p = sub.add_parser("diff", help="Diff two snapshots")
    diff_p.add_argument("a")
    diff_p.add_argument("b")

    inspect_p = sub.add_parser("inspect", help="Summarise and validate snapshots")
    inspect_p.add_argument("name", nargs="?", default=None, help="Specific snapshot (omit for all)")
    inspect_p.add_argument("--validate", action="store_true", help="Run validation checks")

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    dispatch = {
        "list": cmd_list,
        "show": cmd_show,
        "delete": cmd_delete,
        "diff": cmd_diff,
        "inspect": cmd_inspect,
    }
    fn = dispatch.get(args.command)
    if fn is None:
        parser.print_help()
        sys.exit(0)
    fn(args)


if __name__ == "__main__":
    main()
