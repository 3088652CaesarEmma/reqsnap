"""Command-line interface for reqsnap."""

import argparse
import json
import sys
from pathlib import Path

from reqsnap.storage import snapshot_path, load_snapshot, _make_key


def cmd_list(args: argparse.Namespace) -> int:
    """List all recorded snapshots in the snap directory."""
    snap_dir = Path(args.snap_dir)
    if not snap_dir.exists():
        print(f"Snapshot directory not found: {snap_dir}", file=sys.stderr)
        return 1

    snapshots = sorted(snap_dir.glob("*.json"))
    if not snapshots:
        print("No snapshots found.")
        return 0

    print(f"Found {len(snapshots)} snapshot(s) in '{snap_dir}':")
    for snap_file in snapshots:
        try:
            data = json.loads(snap_file.read_text())
            method = data.get("request", {}).get("method", "?")
            url = data.get("request", {}).get("url", "?")
            status = data.get("response", {}).get("status_code", "?")
            print(f"  [{method}] {url} -> HTTP {status}  ({snap_file.name})")
        except (json.JSONDecodeError, KeyError):
            print(f"  (unreadable) {snap_file.name}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    """Show details of a single snapshot by method + URL."""
    snap_dir = Path(args.snap_dir)
    key = _make_key(args.method.upper(), args.url, args.body or b"")
    path = snapshot_path(snap_dir, key)

    if not path.exists():
        print(f"No snapshot found for {args.method.upper()} {args.url}", file=sys.stderr)
        return 1

    data = load_snapshot(snap_dir, key)
    print(json.dumps(data, indent=2))
    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    """Delete a snapshot by method + URL."""
    snap_dir = Path(args.snap_dir)
    key = _make_key(args.method.upper(), args.url, args.body or b"")
    path = snapshot_path(snap_dir, key)

    if not path.exists():
        print(f"No snapshot found for {args.method.upper()} {args.url}", file=sys.stderr)
        return 1

    path.unlink()
    print(f"Deleted snapshot: {path.name}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reqsnap",
        description="HTTP request recorder and replay tool.",
    )
    parser.add_argument("--snap-dir", default=".reqsnap", help="Snapshot storage directory")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List recorded snapshots")

    show_p = sub.add_parser("show", help="Show a snapshot")
    show_p.add_argument("method", help="HTTP method (e.g. GET)")
    show_p.add_argument("url", help="Request URL")
    show_p.add_argument("--body", default=b"", type=lambda x: x.encode(), help="Request body")

    del_p = sub.add_parser("delete", help="Delete a snapshot")
    del_p.add_argument("method", help="HTTP method (e.g. GET)")
    del_p.add_argument("url", help="Request URL")
    del_p.add_argument("--body", default=b"", type=lambda x: x.encode(), help="Request body")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    handlers = {"list": cmd_list, "show": cmd_show, "delete": cmd_delete}
    sys.exit(handlers[args.command](args))


if __name__ == "__main__":
    main()
