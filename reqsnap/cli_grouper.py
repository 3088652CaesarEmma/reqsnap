"""CLI commands for snapshot grouping."""

from __future__ import annotations

import argparse
from pathlib import Path

from reqsnap.grouper import format_groups, group_snapshots


def cmd_group(args: argparse.Namespace) -> None:
    """Group snapshots and print the result."""
    snap_dir = Path(args.snap_dir)
    if not snap_dir.exists():
        print(f"Snapshot directory not found: {snap_dir}")
        return

    try:
        groups = group_snapshots(snap_dir, by=args.by)
    except ValueError as exc:
        print(f"Error: {exc}")
        return

    print(format_groups(groups))


def register_grouper_commands(
    subparsers: argparse._SubParsersAction,  # type: ignore[type-arg]
    snap_dir: str,
) -> None:
    """Attach the *group* sub-command to *subparsers*."""
    p = subparsers.add_parser(
        "group",
        help="Group snapshots by host, method, or status code.",
    )
    p.add_argument(
        "--by",
        choices=["host", "method", "status"],
        default="host",
        help="Dimension to group by (default: host).",
    )
    p.add_argument(
        "--snap-dir",
        default=snap_dir,
        help="Directory containing snapshots.",
    )
    p.set_defaults(func=cmd_group)
