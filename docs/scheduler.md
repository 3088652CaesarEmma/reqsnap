# Snapshot Expiry & TTL Scheduling

reqsnap supports attaching a **time-to-live (TTL)** to any recorded snapshot.
Once a snapshot's TTL has elapsed it is considered *expired* and can be
automatically purged from the snapshot directory.

## How it works

Expiry metadata is stored alongside your snapshots in a single file:

```
<snap_dir>/.expiry.json
```

Each entry maps a snapshot key to a Unix timestamp representing the moment
the snapshot expires.

## Python API

```python
from pathlib import Path
from reqsnap.scheduler import set_expiry, is_expired, purge_expired

snap_dir = Path(".reqsnap")

# Give snapshot key "abc123" a 10-minute TTL
set_expiry(snap_dir, "abc123", ttl_seconds=600)

# Check whether it has expired yet
if is_expired(snap_dir, "abc123"):
    print("Snapshot is stale")

# Remove all expired snapshots and return their keys
purged = purge_expired(snap_dir)
print(f"Purged {len(purged)} snapshot(s)")
```

## CLI commands

| Command | Description |
|---|---|
| `reqsnap expire-set <key> <ttl>` | Attach a TTL (seconds) to a snapshot |
| `reqsnap expire-show <key>` | Show remaining time or expiry status |
| `reqsnap expire-remove <key>` | Remove the TTL from a snapshot |
| `reqsnap purge` | Delete all expired snapshots |

### Examples

```bash
# Set a 1-hour TTL on a snapshot
reqsnap expire-set GET_api_users_abc123 3600

# Check its status
reqsnap expire-show GET_api_users_abc123
# GET_api_users_abc123: expires in 3598s (timestamp=1718000000.00)

# Purge everything that has expired
reqsnap purge
# Purged: GET_api_users_oldkey
# 1 snapshot(s) purged.
```

## Notes

- Snapshots without an expiry entry are **never** automatically purged.
- Purging only removes the `.json` snapshot file and the expiry entry;
  tag metadata (`.tags.json`) is unaffected.
- TTL scheduling does **not** run automatically in the background; call
  `purge_expired()` or `reqsnap purge` explicitly when needed.
