"""Load and validate reqsnap configuration from a TOML or dict source."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_SNAP_DIR = ".reqsnap"
DEFAULT_MODE = "record"


@dataclass
class ReqSnapConfig:
    snap_dir: Path = field(default_factory=lambda: Path(DEFAULT_SNAP_DIR))
    mode: str = DEFAULT_MODE
    sensitive_headers: set[str] = field(default_factory=set)
    sensitive_params: set[str] = field(default_factory=set)
    redact: bool = False

    def __post_init__(self) -> None:
        valid_modes = {"record", "replay", "passthrough"}
        if self.mode not in valid_modes:
            raise ValueError(
                f"Invalid mode {self.mode!r}. Must be one of {sorted(valid_modes)}."
            )
        self.snap_dir = Path(self.snap_dir)


def _from_dict(data: dict[str, Any]) -> ReqSnapConfig:
    """Build a :class:`ReqSnapConfig` from a plain dictionary."""
    return ReqSnapConfig(
        snap_dir=Path(data.get("snap_dir", DEFAULT_SNAP_DIR)),
        mode=data.get("mode", DEFAULT_MODE),
        sensitive_headers=set(data.get("sensitive_headers", [])),
        sensitive_params=set(data.get("sensitive_params", [])),
        redact=bool(data.get("redact", False)),
    )


def load_config(path: str | Path | None = None) -> ReqSnapConfig:
    """Load configuration from *path* (a TOML file) or fall back to defaults.

    Environment variables override file settings:
      - REQSNAP_SNAP_DIR
      - REQSNAP_MODE
      - REQSNAP_REDACT  ("1" / "true" to enable)
    """
    data: dict[str, Any] = {}

    if path is not None:
        path = Path(path)
        if path.exists():
            try:
                import tomllib  # Python 3.11+
            except ImportError:  # pragma: no cover
                import tomli as tomllib  # type: ignore[no-reuse-imports]
            with path.open("rb") as fh:
                raw = tomllib.load(fh)
            data = raw.get("tool", {}).get("reqsnap", raw)

    # Environment variable overrides
    if snap_dir_env := os.environ.get("REQSNAP_SNAP_DIR"):
        data["snap_dir"] = snap_dir_env
    if mode_env := os.environ.get("REQSNAP_MODE"):
        data["mode"] = mode_env
    if redact_env := os.environ.get("REQSNAP_REDACT"):
        data["redact"] = redact_env.lower() in {"1", "true", "yes"}

    return _from_dict(data)
