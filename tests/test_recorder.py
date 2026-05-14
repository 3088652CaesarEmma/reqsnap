"""Tests for reqsnap.recorder — record and replay transport."""

import json
import pytest
import httpx
from unittest.mock import MagicMock, patch

from reqsnap.recorder import ReqSnapTransport, recorded_client
from reqsnap.storage import save_snapshot, snapshot_path


@pytest.fixture()
def snap_dir(tmp_path):
    return str(tmp_path / "snaps")


def _fake_inner_transport(status=200, body="hello", headers=None):
    """Build a mock BaseTransport that returns a fixed response."""
    transport = MagicMock(spec=httpx.BaseTransport)
    response = httpx.Response(
        status_code=status,
        content=body.encode(),
        headers=headers or {"content-type": "text/plain"},
    )
    response.read = MagicMock(return_value=None)  # already read
    transport.handle_request.return_value = response
    return transport


class TestReqSnapTransportInit:
    def test_invalid_mode_raises(self, snap_dir):
        with pytest.raises(ValueError, match="mode must be"):
            ReqSnapTransport(snap_dir=snap_dir, mode="invalid")

    def test_valid_modes_accepted(self, snap_dir):
        for mode in ("record", "replay"):
            t = ReqSnapTransport(snap_dir=snap_dir, mode=mode)
            assert t.mode == mode


class TestRecordMode:
    def test_record_saves_snapshot(self, snap_dir):
        inner = _fake_inner_transport(status=200, body='{"ok": true}')
        transport = ReqSnapTransport(snap_dir=snap_dir, mode="record", inner=inner)

        request = httpx.Request("GET", "https://api.example.com/items")
        response = transport.handle_request(request)

        assert response.status_code == 200
        inner.handle_request.assert_called_once()

        snap = snapshot_path("https://api.example.com/items", "GET", b"", snap_dir=snap_dir)
        assert snap.exists(), "Snapshot file should have been written"

    def test_record_returns_real_response(self, snap_dir):
        inner = _fake_inner_transport(status=404, body="not found")
        transport = ReqSnapTransport(snap_dir=snap_dir, mode="record", inner=inner)

        request = httpx.Request("GET", "https://api.example.com/missing")
        response = transport.handle_request(request)
        assert response.status_code == 404


class TestReplayMode:
    def test_replay_returns_saved_data(self, snap_dir):
        save_snapshot(
            url="https://api.example.com/users",
            method="GET",
            request_body=b"",
            status_code=200,
            response_headers={"content-type": "application/json"},
            response_body='{"users": []}',
            snap_dir=snap_dir,
        )
        transport = ReqSnapTransport(snap_dir=snap_dir, mode="replay")
        request = httpx.Request("GET", "https://api.example.com/users")
        response = transport.handle_request(request)

        assert response.status_code == 200
        assert "users" in response.text

    def test_replay_raises_when_no_snapshot(self, snap_dir):
        transport = ReqSnapTransport(snap_dir=snap_dir, mode="replay")
        request = httpx.Request("GET", "https://api.example.com/nonexistent")
        with pytest.raises(FileNotFoundError, match="No snapshot found"):
            transport.handle_request(request)


class TestRecordedClient:
    def test_returns_httpx_client(self, snap_dir):
        client = recorded_client(snap_dir=snap_dir, mode="replay")
        assert isinstance(client, httpx.Client)
