"""Tests for reqsnap.config."""

import os
from pathlib import Path

import pytest

from reqsnap.config import (
    DEFAULT_MODE,
    DEFAULT_SNAP_DIR,
    ReqSnapConfig,
    load_config,
    _from_dict,
)


# ---------------------------------------------------------------------------
# ReqSnapConfig dataclass
# ---------------------------------------------------------------------------

def test_default_values():
    cfg = ReqSnapConfig()
    assert cfg.snap_dir == Path(DEFAULT_SNAP_DIR)
    assert cfg.mode == DEFAULT_MODE
    assert cfg.redact is False
    assert cfg.sensitive_headers == set()
    assert cfg.sensitive_params == set()


def test_invalid_mode_raises():
    with pytest.raises(ValueError, match="Invalid mode"):
        ReqSnapConfig(mode="unknown")


def test_snap_dir_coerced_to_path():
    cfg = ReqSnapConfig(snap_dir="/tmp/snaps")  # type: ignore[arg-type]
    assert isinstance(cfg.snap_dir, Path)


# ---------------------------------------------------------------------------
# _from_dict
# ---------------------------------------------------------------------------

def test_from_dict_full():
    cfg = _from_dict(
        {
            "snap_dir": "/tmp/snaps",
            "mode": "replay",
            "sensitive_headers": ["x-api-key"],
            "sensitive_params": ["token"],
            "redact": True,
        }
    )
    assert cfg.snap_dir == Path("/tmp/snaps")
    assert cfg.mode == "replay"
    assert "x-api-key" in cfg.sensitive_headers
    assert "token" in cfg.sensitive_params
    assert cfg.redact is True


def test_from_dict_empty_uses_defaults():
    cfg = _from_dict({})
    assert cfg.mode == DEFAULT_MODE
    assert cfg.snap_dir == Path(DEFAULT_SNAP_DIR)


# ---------------------------------------------------------------------------
# load_config — no file
# ---------------------------------------------------------------------------

def test_load_config_no_file_returns_defaults():
    cfg = load_config(path=None)
    assert cfg.mode == DEFAULT_MODE


def test_load_config_nonexistent_path_returns_defaults(tmp_path):
    cfg = load_config(path=tmp_path / "nonexistent.toml")
    assert cfg.mode == DEFAULT_MODE


# ---------------------------------------------------------------------------
# load_config — environment variable overrides
# ---------------------------------------------------------------------------

def test_env_override_snap_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("REQSNAP_SNAP_DIR", str(tmp_path / "env_snaps"))
    cfg = load_config()
    assert cfg.snap_dir == tmp_path / "env_snaps"


def test_env_override_mode(monkeypatch):
    monkeypatch.setenv("REQSNAP_MODE", "replay")
    cfg = load_config()
    assert cfg.mode == "replay"


def test_env_override_redact_true(monkeypatch):
    monkeypatch.setenv("REQSNAP_REDACT", "true")
    cfg = load_config()
    assert cfg.redact is True


def test_env_override_redact_false(monkeypatch):
    monkeypatch.setenv("REQSNAP_REDACT", "0")
    cfg = load_config()
    assert cfg.redact is False


# ---------------------------------------------------------------------------
# load_config — TOML file
# ---------------------------------------------------------------------------

def test_load_config_from_toml(tmp_path):
    toml_file = tmp_path / "pyproject.toml"
    toml_file.write_text(
        '[tool.reqsnap]\nmode = "passthrough"\nredact = true\n',
        encoding="utf-8",
    )
    cfg = load_config(path=toml_file)
    assert cfg.mode == "passthrough"
    assert cfg.redact is True
