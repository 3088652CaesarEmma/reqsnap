"""Tests for reqsnap.replayer — snapshot-backed HTTP replay server."""

from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest
import urllib.request
import urllib.error

from reqsnap.replayer import start_replay_server
from reqsnap.storage import save_snapshot


@pytest.fixture()
def snap_dir(tmp_path: Path) -> Path:
    d = tmp_path / "snaps"
    d.mkdir()
    return d


def _make_snapshot(method, url, status, resp_body, resp_headers=None):
    return {
        "request": {"method": method, "url": url, "headers": {}, "body": None},
        "response": {
            "status_code": status,
            "headers": resp_headers or {"Content-Type": "application/json"},
            "body": resp_body,
        },
    }


@pytest.fixture()
def running_server(snap_dir):
    """Start a replay server in a background thread; yield (server, base_url)."""
    save_snapshot(
        snap_dir,
        _make_snapshot("GET", "http://example.com/hello", 200, json.dumps({"msg": "hi"})),
    )
    server = start_replay_server(snap_dir, host="127.0.0.1", port=0)
    port = server.server_address[1]
    t = threading.Thread(target=server.handle_request, daemon=True)
    t.start()
    yield server, f"http://127.0.0.1:{port}"
    server.server_close()


def test_start_replay_server_returns_server(snap_dir):
    server = start_replay_server(snap_dir, port=0)
    assert server is not None
    server.server_close()


def test_server_binds_to_requested_port(snap_dir):
    server = start_replay_server(snap_dir, host="127.0.0.1", port=0)
    host, port = server.server_address
    assert host == "127.0.0.1"
    assert port > 0
    server.server_close()


def test_matched_request_returns_snapshot_status(running_server):
    server, base = running_server
    with urllib.request.urlopen(f"{base}/hello") as resp:
        assert resp.status == 200


def test_matched_request_returns_snapshot_body(running_server):
    server, base = running_server
    with urllib.request.urlopen(f"{base}/hello") as resp:
        data = json.loads(resp.read())
    assert data == {"msg": "hi"}


def test_unmatched_request_returns_404(running_server):
    server, base = running_server
    # We need a second handle_request call for the 404 path
    t = threading.Thread(target=server.handle_request, daemon=True)
    t.start()
    try:
        urllib.request.urlopen(f"{base}/not-found")
        pytest.fail("Expected HTTPError")
    except urllib.error.HTTPError as exc:
        assert exc.code == 404


def test_unmatched_request_body_contains_error(running_server):
    server, base = running_server
    t = threading.Thread(target=server.handle_request, daemon=True)
    t.start()
    try:
        urllib.request.urlopen(f"{base}/missing")
    except urllib.error.HTTPError as exc:
        body = json.loads(exc.read())
        assert "error" in body
