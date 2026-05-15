# Snapshot Tagging

reqsnap lets you attach arbitrary text labels ("tags") to recorded snapshots.
Tags are stored in a single `.tags.json` file inside your snapshot directory and
never touch the snapshot files themselves.

## Python API

```python
from pathlib import Path
from reqsnap.tagger import add_tag, remove_tag, get_tags, filter_by_tag, all_tags

snap_dir = Path(".reqsnap")

# Attach a tag to a snapshot key
add_tag(snap_dir, "a3f9c1d2", "smoke")
add_tag(snap_dir, "a3f9c1d2", "auth")

# Retrieve tags for a key
print(get_tags(snap_dir, "a3f9c1d2"))   # ['smoke', 'auth']

# Find all snapshots carrying a specific tag
keys = filter_by_tag(snap_dir, "smoke")

# List every tag used across all snapshots
print(all_tags(snap_dir))  # ['auth', 'smoke']

# Remove a tag
remove_tag(snap_dir, "a3f9c1d2", "auth")
```

## CLI

Tag sub-commands are available once `register_tag_commands` is wired into the
main argument parser.

```
# Add a tag
reqsnap tag-add <key> <tag> [--snap-dir .reqsnap]

# Remove a tag
reqsnap tag-remove <key> <tag> [--snap-dir .reqsnap]

# List all tags
reqsnap tag-list [--snap-dir .reqsnap]

# List tags for a specific snapshot
reqsnap tag-list --key <key> [--snap-dir .reqsnap]

# Find snapshots with a given tag
reqsnap tag-list --filter <tag> [--snap-dir .reqsnap]
```

## Storage format

`.tags.json` is a plain JSON object mapping snapshot keys to arrays of tag
strings:

```json
{
  "a3f9c1d2": ["smoke", "regression"],
  "b7e2a0f1": ["smoke"]
}
```
