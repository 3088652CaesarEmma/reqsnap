# Snapshot Archiving

The `reqsnap.archiver` module lets you pack recorded snapshots into a portable
`.tar.gz` archive and restore them later.  This is useful for sharing fixture
sets between team members or storing baselines in CI artefact storage.

## Creating an archive

```python
from pathlib import Path
from reqsnap.archiver import create_archive

archive = create_archive(
    snap_dir=Path("./snaps"),
    dest_dir=Path("./archives"),
    label="sprint-42",        # optional, embedded in filename
    tags=["smoke"],           # optional, filter by tag
)
print(f"Archive written to {archive}")
```

The archive filename follows the pattern:

```
reqsnap_archive[_<label>]_<UTC-timestamp>.tar.gz
```

### Tag filtering

Pass a list of tag names via `tags=` to include only snapshots that carry at
least one of those tags (requires a `_tags.json` file produced by the tagging
module).  Metadata files (`_tags.json`, `_expiry.json`) are always included
when present.

## Restoring an archive

```python
from reqsnap.archiver import restore_archive

written = restore_archive(
    archive_path=Path("./archives/reqsnap_archive_sprint-42_20240101T120000Z.tar.gz"),
    snap_dir=Path("./snaps"),
    overwrite=False,   # skip files that already exist (default)
)
print(f"Restored: {written}")
```

Set `overwrite=True` to replace any existing snapshots with the archived
versions.

## CLI (planned)

Future releases will expose these operations through the `reqsnap` CLI:

```
reqsnap archive create --label sprint-42 --tags smoke
reqsnap archive restore ./archives/reqsnap_archive_sprint-42_*.tar.gz
```
