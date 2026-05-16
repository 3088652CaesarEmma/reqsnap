"""Schema-based validation for recorded snapshots."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

REQUIRED_SNAPSHOT_KEYS = {"method", "url", "status_code", "response_body"}
VALID_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
VALID_STATUS_RANGE = range(100, 600)


@dataclass
class ValidationResult:
    valid: bool
    errors: List[str]

    def __bool__(self) -> bool:
        return self.valid


def _check_required_keys(snapshot: Dict[str, Any]) -> List[str]:
    missing = REQUIRED_SNAPSHOT_KEYS - snapshot.keys()
    return [f"Missing required key: '{k}'" for k in sorted(missing)]


def _check_method(snapshot: Dict[str, Any]) -> List[str]:
    method = snapshot.get("method", "")
    if method not in VALID_METHODS:
        return [f"Invalid HTTP method: '{method}'. Must be one of {sorted(VALID_METHODS)}"]
    return []


def _check_url(snapshot: Dict[str, Any]) -> List[str]:
    url = snapshot.get("url", "")
    if not isinstance(url, str) or not url.startswith(("http://", "https://")):
        return [f"Invalid URL: '{url}'. Must start with http:// or https://"]
    return []


def _check_status_code(snapshot: Dict[str, Any]) -> List[str]:
    code = snapshot.get("status_code")
    if not isinstance(code, int) or code not in VALID_STATUS_RANGE:
        return [f"Invalid status_code: '{code}'. Must be an integer between 100 and 599"]
    return []


def _check_headers(snapshot: Dict[str, Any], field: str) -> List[str]:
    headers = snapshot.get(field)
    if headers is None:
        return []
    if not isinstance(headers, dict):
        return [f"'{field}' must be a dict, got {type(headers).__name__}"]
    bad = [k for k in headers if not isinstance(k, str)]
    if bad:
        return [f"'{field}' keys must be strings, found: {bad}"]
    return []


def validate_snapshot_dict(snapshot: Dict[str, Any]) -> ValidationResult:
    """Validate a snapshot dictionary against the expected schema."""
    errors: List[str] = []
    errors.extend(_check_required_keys(snapshot))
    if "method" in snapshot:
        errors.extend(_check_method(snapshot))
    if "url" in snapshot:
        errors.extend(_check_url(snapshot))
    if "status_code" in snapshot:
        errors.extend(_check_status_code(snapshot))
    errors.extend(_check_headers(snapshot, "request_headers"))
    errors.extend(_check_headers(snapshot, "response_headers"))
    return ValidationResult(valid=len(errors) == 0, errors=errors)


def validate_snapshot_file(path: Path) -> ValidationResult:
    """Load a snapshot JSON file and validate its contents."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return ValidationResult(valid=False, errors=[f"Could not read snapshot: {exc}"])
    return validate_snapshot_dict(data)


def validate_directory(snap_dir: Path) -> Dict[str, ValidationResult]:
    """Validate all snapshot files in a directory. Returns a mapping of filename -> result."""
    results: Dict[str, ValidationResult] = {}
    for snap_file in sorted(snap_dir.glob("*.json")):
        results[snap_file.name] = validate_snapshot_file(snap_file)
    return results
