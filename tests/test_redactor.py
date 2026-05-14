"""Tests for reqsnap.redactor."""

import pytest

from reqsnap.redactor import (
    REDACTED,
    redact_headers,
    redact_query_params,
    redact_snapshot,
)


# ---------------------------------------------------------------------------
# redact_headers
# ---------------------------------------------------------------------------

def test_redact_headers_sensitive_replaced():
    headers = {"Authorization": "Bearer secret", "Content-Type": "application/json"}
    result = redact_headers(headers)
    assert result["Authorization"] == REDACTED
    assert result["Content-Type"] == "application/json"


def test_redact_headers_case_insensitive_key():
    headers = {"X-API-KEY": "my-key"}
    result = redact_headers(headers)
    assert result["X-API-KEY"] == REDACTED


def test_redact_headers_none_returns_empty():
    assert redact_headers(None) == {}


def test_redact_headers_custom_sensitive():
    headers = {"X-Custom-Secret": "shh", "Accept": "*/*"}
    result = redact_headers(headers, sensitive={"x-custom-secret"})
    assert result["X-Custom-Secret"] == REDACTED
    assert result["Accept"] == "*/*"


def test_redact_headers_does_not_mutate_original():
    headers = {"Authorization": "Bearer token"}
    redact_headers(headers)
    assert headers["Authorization"] == "Bearer token"


# ---------------------------------------------------------------------------
# redact_query_params
# ---------------------------------------------------------------------------

def test_redact_query_params_replaces_sensitive():
    url = "https://api.example.com/data?api_key=secret&page=2"
    result = redact_query_params(url, sensitive_params={"api_key"})
    assert "api_key=" + REDACTED in result
    assert "page=2" in result


def test_redact_query_params_no_sensitive_returns_url():
    url = "https://api.example.com/data?foo=bar"
    assert redact_query_params(url, sensitive_params=None) == url


def test_redact_query_params_case_insensitive():
    url = "https://api.example.com/?Token=abc123"
    result = redact_query_params(url, sensitive_params={"token"})
    assert REDACTED in result


# ---------------------------------------------------------------------------
# redact_snapshot
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_snapshot():
    return {
        "request": {
            "method": "GET",
            "url": "https://api.example.com/users?api_key=secret&limit=10",
            "headers": {"Authorization": "Bearer tok", "Accept": "application/json"},
            "body": None,
        },
        "response": {
            "status_code": 200,
            "headers": {"Set-Cookie": "session=abc", "Content-Type": "application/json"},
            "body": '{"id": 1}',
        },
    }


def test_redact_snapshot_request_headers(sample_snapshot):
    result = redact_snapshot(sample_snapshot)
    assert result["request"]["headers"]["Authorization"] == REDACTED
    assert result["request"]["headers"]["Accept"] == "application/json"


def test_redact_snapshot_response_headers(sample_snapshot):
    result = redact_snapshot(sample_snapshot)
    assert result["response"]["headers"]["Set-Cookie"] == REDACTED


def test_redact_snapshot_does_not_mutate_original(sample_snapshot):
    redact_snapshot(sample_snapshot, sensitive_params={"api_key"})
    assert "secret" in sample_snapshot["request"]["url"]


def test_redact_snapshot_url_params(sample_snapshot):
    result = redact_snapshot(sample_snapshot, sensitive_params={"api_key"})
    assert REDACTED in result["request"]["url"]
    assert "limit=10" in result["request"]["url"]
