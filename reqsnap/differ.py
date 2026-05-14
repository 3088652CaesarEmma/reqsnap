"""Snapshot diff utilities for comparing recorded HTTP snapshots."""

from __future__ import annotations

import json
from typing import Any


def _parse_body(body: str | None) -> Any:
    """Try to parse body as JSON; fall back to raw string."""
    if body is None:
        return None
    try:
        return json.loads(body)
    except (json.JSONDecodeError, TypeError):
        return body


def _diff_headers(a: dict, b: dict) -> list[dict]:
    """Return a list of header differences between two snapshots."""
    keys = set(a) | set(b)
    diffs = []
    for key in sorted(keys):
        val_a = a.get(key)
        val_b = b.get(key)
        if val_a != val_b:
            diffs.append({"header": key, "a": val_a, "b": val_b})
    return diffs


def _diff_body(a: str | None, b: str | None) -> dict | None:
    """Return a body diff summary, or None if bodies are identical."""
    parsed_a = _parse_body(a)
    parsed_b = _parse_body(b)
    if parsed_a == parsed_b:
        return None
    return {"a": parsed_a, "b": parsed_b}


def diff_snapshots(snap_a: dict, snap_b: dict) -> dict:
    """Compare two snapshot dicts and return a structured diff.

    Args:
        snap_a: First snapshot (baseline).
        snap_b: Second snapshot (comparison).

    Returns:
        A dict with keys 'request' and 'response', each containing
        detected differences.  Empty sub-dicts mean no differences.
    """
    req_a = snap_a.get("request", {})
    req_b = snap_b.get("request", {})
    resp_a = snap_a.get("response", {})
    resp_b = snap_b.get("response", {})

    request_diff: dict = {}
    if req_a.get("method") != req_b.get("method"):
        request_diff["method"] = {"a": req_a.get("method"), "b": req_b.get("method")}
    if req_a.get("url") != req_b.get("url"):
        request_diff["url"] = {"a": req_a.get("url"), "b": req_b.get("url")}
    header_diffs = _diff_headers(
        req_a.get("headers") or {}, req_b.get("headers") or {}
    )
    if header_diffs:
        request_diff["headers"] = header_diffs
    body_diff = _diff_body(req_a.get("body"), req_b.get("body"))
    if body_diff:
        request_diff["body"] = body_diff

    response_diff: dict = {}
    if resp_a.get("status_code") != resp_b.get("status_code"):
        response_diff["status_code"] = {
            "a": resp_a.get("status_code"),
            "b": resp_b.get("status_code"),
        }
    resp_header_diffs = _diff_headers(
        resp_a.get("headers") or {}, resp_b.get("headers") or {}
    )
    if resp_header_diffs:
        response_diff["headers"] = resp_header_diffs
    resp_body_diff = _diff_body(resp_a.get("body"), resp_b.get("body"))
    if resp_body_diff:
        response_diff["body"] = resp_body_diff

    return {"request": request_diff, "response": response_diff}


def is_identical(diff: dict) -> bool:
    """Return True when a diff produced by diff_snapshots shows no changes."""
    return not diff["request"] and not diff["response"]
