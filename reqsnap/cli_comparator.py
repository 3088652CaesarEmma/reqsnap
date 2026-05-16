"""CLI commands for snapshot comparison."""

from __future__ import annotations

import argparse
from pathlib import Path

from reqsnap.comparator import compare_snapshots


def cmd_compare(args: argparse.Namespace) -> None:
    snap_dir = Path(args.snap_dir)
    try:
        report = compare_snapshots(snap_dir, args.key_a, args.key_b)
    except FileNotFoundError as exc:
        print(f"Error: {exc}")
        return

    print(f"Comparing '{report.key_a}'  vs  '{report.key_b}'")
    print()

    if report.is_identical:
        print("Snapshots are identical.")
        return

    if report.matching_fields:
        print(f"Matching fields ({len(report.matching_fields)}):")
        for f in report.matching_fields:
            print(f"  = {f}")
        print()

    if report.differing_fields:
        print(f"Differing fields ({len(report.differing_fields)}):")
        for f, vals in report.differing_fields.items():
            print(f"  ~ {f}")
            print(f"      a: {vals['a']}")
            print(f"      b: {vals['b']}")
        print()

    if report.only_in_a:
        print(f"Only in '{report.key_a}':")
        for f in report.only_in_a:
            print(f"  < {f}")
        print()

    if report.only_in_b:
        print(f"Only in '{report.key_b}':")
        for f in report.only_in_b:
            print(f"  > {f}")
        print()


def register_comparator_commands(
    subparsers: argparse._SubParsersAction,
    snap_dir: str,
) -> None:
    p = subparsers.add_parser("compare", help="Compare two snapshots side-by-side")
    p.add_argument("key_a", help="First snapshot key")
    p.add_argument("key_b", help="Second snapshot key")
    p.add_argument("--snap-dir", default=snap_dir)
    p.set_defaults(func=cmd_compare)
