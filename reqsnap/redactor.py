"""Redact sensitive fields from recorded snapshots before saving."""

from __future__ import annotations

import re
from typing import Any

# Default header names that should be redacted
DEFAULT_SENSITIVE_HEADERS = {
    "authorization",
    "x-api-key",
    "x-auth-token",
    "cookie",
    "set-cookie",
    "proxy-authorization",
}

REDACTED = "[REDACTED]"


def redact_headers(
    headers: dict[str, str] | None,
    sensitive: set[str] | None = None,
) -> dict[str, str]:
    """Return a copy of *headers* with sensitive values replaced."""
    if not headers:
        return {}
    if sensitive is None:
        sensitive = DEFAULT_SENSITIVE_HEADERS
    return {
        k: (REDACTED if k.lower() in sensitive else v)
        for k, v in headers.items()
    }


def redact_query_params(
    url: str,
    sensitive_params: set[str] | None = None,
) -> str:
    """Replace sensitive query-parameter values in *url* with REDACTED."""
    if not sensitive_params:
        return url

    def _replace(match: re.Match) -> str:  # type: ignore[type-arg]
        key = match.group(1)
        if key.lower() in {p.lower() for p in sensitive_params}:
            return f"{key}={REDACTED}"
        return match.group(0)

    return re.sub(r"([^&=?]+)=([^&]*)", _replace, url)


def redact_snapshot(
    snapshot: dict[str, Any],
    sensitive_headers: set[str] | None = None,
    sensitive_params: set[str] | None = None,
) -> dict[str, Any]:
    """Return a deep-copy of *snapshot* with sensitive data redacted."""
    import copy

    snap = copy.deepcopy(snapshot)

    # Redact request headers
    req = snap.get("request", {})
    req["headers"] = redact_headers(req.get("headers"), sensitive_headers)
    req["url"] = redact_query_params(req.get("url", ""), sensitive_params)

    # Redact response headers
    resp = snap.get("response", {})
    resp["headers"] = redact_headers(resp.get("headers"), sensitive_headers)

    return snap
