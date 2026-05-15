"""Tests for reqsnap.transformer."""

from __future__ import annotations

import pytest

from reqsnap.transformer import (
    _apply_template,
    inject_headers,
    override_status,
    template_body,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _snap(status: int = 200, body: str = "", headers: dict | None = None) -> dict:
    return {
        "request": {"method": "GET", "url": "http://example.com", "headers": {}},
        "response": {
            "status_code": status,
            "headers": headers or {"content-type": "application/json"},
            "body": body,
        },
    }


# ---------------------------------------------------------------------------
# _apply_template
# ---------------------------------------------------------------------------

def test_apply_template_replaces_known_key():
    assert _apply_template("Hello {{name}}!", {"name": "world"}) == "Hello world!"


def test_apply_template_leaves_unknown_key_unchanged():
    result = _apply_template("{{unknown}}", {})
    assert result == "{{unknown}}"


def test_apply_template_handles_whitespace_around_key():
    assert _apply_template("{{ key }}", {"key": "v"}) == "v"


def test_apply_template_multiple_placeholders():
    result = _apply_template("{{a}}-{{b}}", {"a": "1", "b": "2"})
    assert result == "1-2"


# ---------------------------------------------------------------------------
# override_status
# ---------------------------------------------------------------------------

def test_override_status_changes_code():
    snap = _snap(status=200)
    result = override_status(snap, 404)
    assert result["response"]["status_code"] == 404


def test_override_status_does_not_mutate_original():
    snap = _snap(status=200)
    override_status(snap, 500)
    assert snap["response"]["status_code"] == 200


def test_override_status_preserves_other_fields():
    snap = _snap(status=200, body="ok")
    result = override_status(snap, 201)
    assert result["response"]["body"] == "ok"


# ---------------------------------------------------------------------------
# inject_headers
# ---------------------------------------------------------------------------

def test_inject_headers_adds_new_header():
    snap = _snap()
    result = inject_headers(snap, {"X-Custom": "yes"})
    assert result["response"]["headers"]["X-Custom"] == "yes"


def test_inject_headers_overwrites_existing_case_insensitive():
    snap = _snap(headers={"Content-Type": "text/plain"})
    result = inject_headers(snap, {"content-type": "application/json"})
    headers = result["response"]["headers"]
    values = list(headers.values())
    assert "application/json" in values


def test_inject_headers_does_not_mutate_original():
    snap = _snap()
    inject_headers(snap, {"X-Test": "1"})
    assert "X-Test" not in snap["response"]["headers"]


def test_inject_headers_invalid_target_raises():
    with pytest.raises(ValueError, match="target"):
        inject_headers(_snap(), {}, target="body")


# ---------------------------------------------------------------------------
# template_body
# ---------------------------------------------------------------------------

def test_template_body_expands_placeholder():
    snap = _snap(body='{"user": "{{name}}"}')
    result = template_body(snap, {"name": "alice"})
    assert result["response"]["body"] == '{"user": "alice"}'


def test_template_body_none_body_unchanged():
    snap = _snap()
    snap["response"]["body"] = None
    result = template_body(snap, {"key": "val"})
    assert result["response"]["body"] is None


def test_template_body_does_not_mutate_original():
    snap = _snap(body="{{x}}")
    template_body(snap, {"x": "replaced"})
    assert snap["response"]["body"] == "{{x}}"


def test_template_body_invalid_target_raises():
    with pytest.raises(ValueError):
        template_body(_snap(), {}, target="headers")
