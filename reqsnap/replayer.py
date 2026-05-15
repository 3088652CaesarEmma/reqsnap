"""Replay recorded snapshots as a local HTTP server for API mocking."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional
from pathlib import Path

from reqsnap.matcher import find_match, list_snapshots
from reqsnap.storage import load_snapshot


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9999


def _make_handler(snap_dir: Path):
    """Return a request handler class bound to the given snapshot directory."""

    class _Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):  # suppress default stderr logging
            pass

        def _read_body(self) -> Optional[str]:
            length = int(self.headers.get("Content-Length", 0))
            if length:
                return self.rfile.read(length).decode("utf-8", errors="replace")
            return None

        def _dispatch(self):
            body = self._read_body()
            headers = dict(self.headers)
            snapshots = list_snapshots(snap_dir)
            match = find_match(
                method=self.command,
                url=self.path,
                headers=headers,
                body=body,
                snapshots=snapshots,
            )
            if match is None:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                payload = json.dumps({"error": "No matching snapshot found"}).encode()
                self.wfile.write(payload)
                return

            snap = load_snapshot(snap_dir, match)
            status = snap["response"]["status_code"]
            resp_headers = snap["response"].get("headers", {})
            resp_body = snap["response"].get("body", "")

            self.send_response(status)
            for key, value in resp_headers.items():
                self.send_header(key, value)
            self.end_headers()
            if resp_body:
                self.wfile.write(
                    resp_body.encode("utf-8") if isinstance(resp_body, str) else resp_body
                )

        def do_GET(self): self._dispatch()
        def do_POST(self): self._dispatch()
        def do_PUT(self): self._dispatch()
        def do_PATCH(self): self._dispatch()
        def do_DELETE(self): self._dispatch()
        def do_HEAD(self): self._dispatch()
        def do_OPTIONS(self): self._dispatch()

    return _Handler


def start_replay_server(
    snap_dir: Path,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> HTTPServer:
    """Create and return an HTTPServer that replays snapshots."""
    handler = _make_handler(snap_dir)
    server = HTTPServer((host, port), handler)
    return server
