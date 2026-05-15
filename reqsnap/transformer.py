"""Response transformation utilities for reqsnap.

Allows modifying snapshots before replay, e.g. overriding status codes,
injecting headers, or templating response bodies.
"""

from __future__ import annotations

import re
import string
from typing import Any, Dict, Optional


def _apply_template(text: str, variables: Dict[str, str]) -> str:
    """Substitute {{key}} placeholders in *text* using *variables*."""
    def _replace(match: re.Match) -> str:
        key = match.group(1).strip()
        return variables.get(key, match.group(0))

    return re.sub(r"\{\{(.+?)\}\}", _replace, text)


def override_status(snapshot: Dict[str, Any], status_code: int) -> Dict[str, Any]:
    """Return a copy of *snapshot* with the response status code replaced."""
    result = dict(snapshot)
    result["response"] = dict(snapshot.get("response", {}))
    result["response"]["status_code"] = status_code
    return result


def inject_headers(
    snapshot: Dict[str, Any],
    headers: Dict[str, str],
    *,
    target: str = "response",
) -> Dict[str, Any]:
    """Return a copy of *snapshot* with extra *headers* merged into *target*.

    *target* must be ``"request"`` or ``"response"``.
    Existing header values are overwritten when keys collide (case-insensitive).
    """
    if target not in ("request", "response"):
        raise ValueError(f"target must be 'request' or 'response', got {target!r}")

    result = dict(snapshot)
    section = dict(snapshot.get(target, {}))
    existing: Dict[str, str] = dict(section.get("headers") or {})

    lower_keys = {k.lower(): k for k in existing}
    for key, value in headers.items():
        canonical = lower_keys.get(key.lower(), key)
        existing[canonical] = value

    section["headers"] = existing
    result[target] = section
    return result


def template_body(
    snapshot: Dict[str, Any],
    variables: Dict[str, str],
    *,
    target: str = "response",
) -> Dict[str, Any]:
    """Return a copy of *snapshot* with ``{{placeholders}}`` in the body expanded."""
    if target not in ("request", "response"):
        raise ValueError(f"target must be 'request' or 'response', got {target!r}")

    result = dict(snapshot)
    section = dict(snapshot.get(target, {}))
    body: Optional[str] = section.get("body")

    if body is not None:
        section["body"] = _apply_template(body, variables)

    result[target] = section
    return result
