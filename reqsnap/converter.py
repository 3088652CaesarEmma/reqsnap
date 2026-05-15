"""Convert snapshots between formats (curl, httpie, Python requests)."""

from __future__ import annotations

import json
import shlex
from typing import Any


def _headers_to_curl(headers: dict[str, str]) -> list[str]:
    """Return a list of -H flags for curl."""
    return [f"-H {shlex.quote(f'{k}: {v}')}"] for k, v in headers.items()]


def to_curl(snapshot: dict[str, Any]) -> str:
    """Convert a snapshot request to a curl command string."""
    req = snapshot.get("request", {})
    method: str = req.get("method", "GET").upper()
    url: str = req.get("url", "")
    headers: dict[str, str] = req.get("headers") or {}
    body: str | None = req.get("body")

    parts = ["curl", "-X", shlex.quote(method)]

    for key, value in headers.items():
        parts += ["-H", shlex.quote(f"{key}: {value}")]

    if body:
        parts += ["--data-raw", shlex.quote(body)]

    parts.append(shlex.quote(url))
    return " ".join(parts)


def to_httpie(snapshot: dict[str, Any]) -> str:
    """Convert a snapshot request to an httpie command string."""
    req = snapshot.get("request", {})
    method: str = req.get("method", "GET").upper()
    url: str = req.get("url", "")
    headers: dict[str, str] = req.get("headers") or {}
    body: str | None = req.get("body")

    parts = ["http", method, shlex.quote(url)]

    for key, value in headers.items():
        parts.append(shlex.quote(f"{key}:{value}"))

    if body:
        try:
            parsed = json.loads(body)
            for k, v in (parsed.items() if isinstance(parsed, dict) else {}):
                parts.append(shlex.quote(f"{k}:={json.dumps(v)}"))
        except (json.JSONDecodeError, AttributeError):
            parts += ["<<<", shlex.quote(body)]

    return " ".join(parts)


def to_python_requests(snapshot: dict[str, Any]) -> str:
    """Convert a snapshot request to a Python requests snippet."""
    req = snapshot.get("request", {})
    method: str = req.get("method", "GET").upper()
    url: str = req.get("url", "")
    headers: dict[str, str] = req.get("headers") or {}
    body: str | None = req.get("body")

    lines = ["import requests", ""]
    lines.append(f"url = {url!r}")

    if headers:
        lines.append(f"headers = {json.dumps(headers, indent=4)}")
    else:
        lines.append("headers = {}")

    kwargs = "url, headers=headers"
    if body:
        try:
            json.loads(body)
            lines.append(f"json_body = {body}")
            kwargs += ", json=json_body"
        except (json.JSONDecodeError, TypeError):
            lines.append(f"data = {body!r}")
            kwargs += ", data=data"

    lines.append(f"response = requests.{method.lower()}({kwargs})")
    return "\n".join(lines)
