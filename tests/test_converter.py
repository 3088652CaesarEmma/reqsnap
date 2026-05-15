"""Tests for reqsnap.converter."""

from __future__ import annotations

import pytest

from reqsnap.converter import to_curl, to_httpie, to_python_requests


def _snap(method="GET", url="https://example.com/api", headers=None, body=None):
    return {
        "request": {
            "method": method,
            "url": url,
            "headers": headers or {},
            "body": body,
        }
    }


# --- to_curl ---

def test_curl_basic_get():
    result = to_curl(_snap())
    assert "curl" in result
    assert "-X" in result
    assert "GET" in result
    assert "https://example.com/api" in result


def test_curl_includes_headers():
    result = to_curl(_snap(headers={"Authorization": "Bearer token123"}))
    assert "Authorization: Bearer token123" in result
    assert "-H" in result


def test_curl_includes_body():
    result = to_curl(_snap(method="POST", body='{"key": "value"}'))
    assert "--data-raw" in result
    assert "key" in result


def test_curl_no_body_omits_data_flag():
    result = to_curl(_snap())
    assert "--data-raw" not in result


# --- to_httpie ---

def test_httpie_basic_get():
    result = to_httpie(_snap())
    assert result.startswith("http GET")
    assert "https://example.com/api" in result


def test_httpie_includes_headers():
    result = to_httpie(_snap(headers={"X-Custom": "yes"}))
    assert "X-Custom:yes" in result


def test_httpie_json_body_expanded():
    result = to_httpie(_snap(method="POST", body='{"name": "alice"}'))
    assert "name" in result


def test_httpie_non_json_body_uses_heredoc():
    result = to_httpie(_snap(method="POST", body="plain text body"))
    assert "<<<" in result
    assert "plain text body" in result


# --- to_python_requests ---

def test_python_requests_basic():
    result = to_python_requests(_snap())
    assert "import requests" in result
    assert "requests.get(" in result


def test_python_requests_post_with_json():
    result = to_python_requests(_snap(method="POST", body='{"x": 1}'))
    assert "requests.post(" in result
    assert "json=json_body" in result


def test_python_requests_post_with_plain_body():
    result = to_python_requests(_snap(method="PUT", body="raw data"))
    assert "data =" in result
    assert "data=data" in result


def test_python_requests_includes_headers():
    result = to_python_requests(_snap(headers={"Accept": "application/json"}))
    assert "Accept" in result
    assert "headers=headers" in result
