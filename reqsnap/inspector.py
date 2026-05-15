"""Snapshot inspector: summarise and validate stored snapshots."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from reqsnap.storage import load_snapshot


def _content_type(headers: dict[str, str] | None) -> str:
    """Return the Content-Type value (lower-cased) or empty string."""
    if not headers:
        return ""
    for key, value in headers.items():
        if key.lower() == "content-type":
            return value.lower()
    return ""


def _is_json(content_type: str) -> bool:
    return "application/json" in content_type


def summarise_snapshot(path: Path) -> dict[str, Any]:
    """Return a human-readable summary dict for a single snapshot file."""
    snap = load_snapshot(path)
    req = snap.get("request", {})
    resp = snap.get("response", {})

    req_ct = _content_type(req.get("headers"))
    resp_ct = _content_type(resp.get("headers"))

    body_size: int | None = None
    raw_body = resp.get("body")
    if isinstance(raw_body, str):
        body_size = len(raw_body.encode())

    return {
        "file": path.name,
        "method": req.get("method", "UNKNOWN").upper(),
        "url": req.get("url", ""),
        "status": resp.get("status_code"),
        "request_content_type": req_ct or None,
        "response_content_type": resp_ct or None,
        "response_body_bytes": body_size,
        "request_is_json": _is_json(req_ct),
        "response_is_json": _is_json(resp_ct),
    }


def validate_snapshot(path: Path) -> list[str]:
    """Return a list of validation warnings for a snapshot file.

    An empty list means the snapshot looks well-formed.
    """
    warnings: list[str] = []
    try:
        snap = load_snapshot(path)
    except Exception as exc:  # noqa: BLE001
        return [f"Cannot load snapshot: {exc}"]

    req = snap.get("request")
    resp = snap.get("response")

    if not req:
        warnings.append("Missing 'request' section.")
    else:
        if not req.get("method"):
            warnings.append("Request is missing 'method'.")
        if not req.get("url"):
            warnings.append("Request is missing 'url'.")

    if not resp:
        warnings.append("Missing 'response' section.")
    else:
        status = resp.get("status_code")
        if status is None:
            warnings.append("Response is missing 'status_code'.")
        elif not isinstance(status, int) or not (100 <= status <= 599):
            warnings.append(f"Response 'status_code' looks invalid: {status!r}.")

        resp_ct = _content_type(resp.get("headers"))
        if _is_json(resp_ct):
            body = resp.get("body")
            if isinstance(body, str):
                try:
                    json.loads(body)
                except json.JSONDecodeError:
                    warnings.append("Response claims JSON content-type but body is not valid JSON.")

    return warnings
