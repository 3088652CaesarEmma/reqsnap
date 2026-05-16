"""Tests for reqsnap.validator."""
import json
import pytest
from pathlib import Path

from reqsnap.validator import (
    validate_snapshot_dict,
    validate_snapshot_file,
    validate_directory,
    ValidationResult,
)


@pytest.fixture()
def snap_dir(tmp_path: Path) -> Path:
    return tmp_path


def _good_snap() -> dict:
    return {
        "method": "GET",
        "url": "https://api.example.com/items",
        "status_code": 200,
        "response_body": '{"ok": true}',
    }


# --- validate_snapshot_dict ---

def test_valid_snapshot_passes():
    result = validate_snapshot_dict(_good_snap())
    assert result.valid is True
    assert result.errors == []


def test_bool_truthy_for_valid():
    assert bool(validate_snapshot_dict(_good_snap())) is True


def test_missing_required_key_reported():
    snap = _good_snap()
    del snap["status_code"]
    result = validate_snapshot_dict(snap)
    assert not result.valid
    assert any("status_code" in e for e in result.errors)


def test_multiple_missing_keys_all_reported():
    result = validate_snapshot_dict({})
    assert not result.valid
    assert len(result.errors) >= 4


def test_invalid_method_reported():
    snap = {**_good_snap(), "method": "FETCH"}
    result = validate_snapshot_dict(snap)
    assert not result.valid
    assert any("FETCH" in e for e in result.errors)


def test_invalid_url_no_scheme():
    snap = {**_good_snap(), "url": "api.example.com/items"}
    result = validate_snapshot_dict(snap)
    assert not result.valid
    assert any("URL" in e for e in result.errors)


def test_status_code_out_of_range():
    snap = {**_good_snap(), "status_code": 99}
    result = validate_snapshot_dict(snap)
    assert not result.valid


def test_status_code_string_invalid():
    snap = {**_good_snap(), "status_code": "200"}
    result = validate_snapshot_dict(snap)
    assert not result.valid


def test_request_headers_non_dict_invalid():
    snap = {**_good_snap(), "request_headers": ["accept: */*"]}
    result = validate_snapshot_dict(snap)
    assert not result.valid
    assert any("request_headers" in e for e in result.errors)


def test_response_headers_valid_dict_passes():
    snap = {**_good_snap(), "response_headers": {"content-type": "application/json"}}
    result = validate_snapshot_dict(snap)
    assert result.valid


# --- validate_snapshot_file ---

def test_validate_file_valid(snap_dir: Path):
    p = snap_dir / "snap.json"
    p.write_text(json.dumps(_good_snap()), encoding="utf-8")
    result = validate_snapshot_file(p)
    assert result.valid


def test_validate_file_missing_returns_error(snap_dir: Path):
    result = validate_snapshot_file(snap_dir / "nonexistent.json")
    assert not result.valid
    assert result.errors


def test_validate_file_bad_json(snap_dir: Path):
    p = snap_dir / "bad.json"
    p.write_text("not json", encoding="utf-8")
    result = validate_snapshot_file(p)
    assert not result.valid


# --- validate_directory ---

def test_validate_directory_returns_all_files(snap_dir: Path):
    for name in ("a.json", "b.json"):
        (snap_dir / name).write_text(json.dumps(_good_snap()), encoding="utf-8")
    results = validate_directory(snap_dir)
    assert set(results.keys()) == {"a.json", "b.json"}


def test_validate_directory_empty(snap_dir: Path):
    assert validate_directory(snap_dir) == {}


def test_validate_directory_mixed_results(snap_dir: Path):
    (snap_dir / "good.json").write_text(json.dumps(_good_snap()), encoding="utf-8")
    bad = {"url": "not-a-url", "status_code": 200, "response_body": ""}
    (snap_dir / "bad.json").write_text(json.dumps(bad), encoding="utf-8")
    results = validate_directory(snap_dir)
    assert results["good.json"].valid is True
    assert results["bad.json"].valid is False
