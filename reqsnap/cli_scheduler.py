"""CLI commands for snapshot TTL / expiry management."""

from __future__ import annotations

import argparse
from pathlib import Path

from reqsnap.scheduler import (
    get_expiry,
    is_expired,
    purge_expired,
    remove_expiry,
    set_expiry,
)

import time


def cmd_expire_set(args: argparse.Namespace) -> None:
    """Attach a TTL to a snapshot key."""
    snap_dir = Path(args.snap_dir)
    set_expiry(snap_dir, args.key, ttl_seconds=args.ttl)
    print(f"Expiry set: {args.key} expires in {args.ttl}s")


def cmd_expire_show(args: argparse.Namespace) -> None:
    """Show the expiry timestamp for a snapshot key."""
    snap_dir = Path(args.snap_dir)
    expiry = get_expiry(snap_dir, args.key)
    if expiry is None:
        print(f"{args.key}: no expiry set")
        return
    remaining = expiry - time.time()
    status = "EXPIRED" if remaining < 0 else f"expires in {remaining:.0f}s"
    print(f"{args.key}: {status} (timestamp={expiry:.2f})")


def cmd_expire_remove(args: argparse.Namespace) -> None:
    """Remove the TTL from a snapshot key."""
    snap_dir = Path(args.snap_dir)
    remove_expiry(snap_dir, args.key)
    print(f"Expiry removed for {args.key}")


def cmd_purge(args: argparse.Namespace) -> None:
    """Delete all expired snapshots from the snapshot directory."""
    snap_dir = Path(args.snap_dir)
    purged = purge_expired(snap_dir)
    if not purged:
        print("No expired snapshots found.")
    else:
        for key in purged:
            print(f"Purged: {key}")
        print(f"{len(purged)} snapshot(s) purged.")


def register_scheduler_commands(subparsers, snap_dir: str) -> None:
    """Attach scheduler sub-commands to the main CLI parser."""
    # expire set
    p_set = subparsers.add_parser("expire-set", help="Set TTL for a snapshot")
    p_set.add_argument("key", help="Snapshot key")
    p_set.add_argument("ttl", type=int, help="TTL in seconds")
    p_set.set_defaults(func=cmd_expire_set, snap_dir=snap_dir)

    # expire show
    p_show = subparsers.add_parser("expire-show", help="Show expiry for a snapshot")
    p_show.add_argument("key", help="Snapshot key")
    p_show.set_defaults(func=cmd_expire_show, snap_dir=snap_dir)

    # expire remove
    p_rm = subparsers.add_parser("expire-remove", help="Remove TTL from a snapshot")
    p_rm.add_argument("key", help="Snapshot key")
    p_rm.set_defaults(func=cmd_expire_remove, snap_dir=snap_dir)

    # purge
    p_purge = subparsers.add_parser("purge", help="Delete all expired snapshots")
    p_purge.set_defaults(func=cmd_purge, snap_dir=snap_dir)
