"""Export and import snapshots to/from HAR (HTTP Archive) format."""

import json
import time
from pathlib import Path
from typing import List, Dict, Any

from .storage import load_snapshot, snapshot_path


def _snapshot_to_har_entry(snap: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a single reqsnap snapshot dict to a HAR entry."""
    request = snap.get("request", {})
    response = snap.get("response", {})

    req_body = request.get("body") or ""
    resp_body = response.get("body") or ""
    resp_content_type = response.get("headers", {}).get("content-type", "application/octet-stream")

    return {
        "startedDateTime": snap.get("recorded_at", ""),
        "time": response.get("elapsed_ms", 0),
        "request": {
            "method": request.get("method", "GET"),
            "url": request.get("url", ""),
            "httpVersion": "HTTP/1.1",
            "headers": [
                {"name": k, "value": v}
                for k, v in (request.get("headers") or {}).items()
            ],
            "queryString": [],
            "postData": {
                "mimeType": request.get("headers", {}).get("content-type", "text/plain"),
                "text": req_body,
            } if req_body else None,
            "bodySize": len(req_body.encode()) if req_body else 0,
            "headersSize": -1,
        },
        "response": {
            "status": response.get("status_code", 200),
            "statusText": "",
            "httpVersion": "HTTP/1.1",
            "headers": [
                {"name": k, "value": v}
                for k, v in (response.get("headers") or {}).items()
            ],
            "content": {
                "size": len(resp_body.encode()) if resp_body else 0,
                "mimeType": resp_content_type,
                "text": resp_body,
            },
            "redirectURL": "",
            "headersSize": -1,
            "bodySize": len(resp_body.encode()) if resp_body else 0,
        },
        "cache": {},
        "timings": {"send": 0, "wait": response.get("elapsed_ms", 0), "receive": 0},
    }


def export_har(snap_dir: Path, keys: List[str] = None) -> Dict[str, Any]:
    """Export snapshots from *snap_dir* as a HAR document.

    If *keys* is provided only those snapshots are included; otherwise all
    snapshots found in the directory are exported.
    """
    entries = []
    if keys is None:
        keys = [p.stem for p in snap_dir.glob("*.json")]

    for key in keys:
        path = snapshot_path(snap_dir, key)
        snap = load_snapshot(snap_dir, key)
        if snap is not None:
            entries.append(_snapshot_to_har_entry(snap))

    return {
        "log": {
            "version": "1.2",
            "creator": {"name": "reqsnap", "version": "0.1.0"},
            "entries": entries,
        }
    }


def export_har_file(snap_dir: Path, output_path: Path, keys: List[str] = None) -> int:
    """Write HAR export to *output_path*. Returns number of entries written."""
    har = export_har(snap_dir, keys=keys)
    output_path.write_text(json.dumps(har, indent=2), encoding="utf-8")
    return len(har["log"]["entries"])
