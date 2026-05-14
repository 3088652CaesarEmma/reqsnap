"""HTTP request recorder that intercepts and snapshots responses."""

import functools
from typing import Callable, Optional

import httpx

from .storage import save_snapshot, load_snapshot, snapshot_path


class ReqSnapTransport(httpx.BaseTransport):
    """Custom HTTPX transport that records or replays HTTP requests."""

    def __init__(
        self,
        snap_dir: str = "snapshots",
        mode: str = "record",
        inner: Optional[httpx.BaseTransport] = None,
    ) -> None:
        """
        Args:
            snap_dir: Directory to store/load snapshots.
            mode: 'record' to hit real API and save, 'replay' to use saved snapshots.
            inner: Underlying transport for real HTTP calls (defaults to HTTPTransport).
        """
        if mode not in ("record", "replay"):
            raise ValueError(f"mode must be 'record' or 'replay', got {mode!r}")
        self.snap_dir = snap_dir
        self.mode = mode
        self._inner = inner or httpx.HTTPTransport()

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        method = request.method
        body = request.content

        if self.mode == "replay":
            data = load_snapshot(url, method, body, snap_dir=self.snap_dir)
            if data is None:
                raise FileNotFoundError(
                    f"No snapshot found for {method} {url}. "
                    "Run in 'record' mode first."
                )
            return httpx.Response(
                status_code=data["status_code"],
                headers=data["headers"],
                content=data["body"].encode() if isinstance(data["body"], str) else data["body"],
            )

        # record mode: perform real request then save
        response = self._inner.handle_request(request)
        response.read()
        save_snapshot(
            url=url,
            method=method,
            request_body=body,
            status_code=response.status_code,
            response_headers=dict(response.headers),
            response_body=response.text,
            snap_dir=self.snap_dir,
        )
        return response


def recorded_client(
    snap_dir: str = "snapshots",
    mode: str = "record",
    **client_kwargs,
) -> httpx.Client:
    """Return an httpx.Client pre-configured with ReqSnapTransport."""
    transport = ReqSnapTransport(snap_dir=snap_dir, mode=mode)
    return httpx.Client(transport=transport, **client_kwargs)
