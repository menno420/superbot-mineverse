"""superbot-mineverse stage-1 backend — read-only walking skeleton.

Serves exactly two things, from the standard library alone (no framework,
no database, no auth, no secrets):

- ``GET /api/snapshot`` — the committed sample snapshot
  (``data/sample_snapshot.json``) as ``application/json``.  A missing or
  unreadable snapshot returns an honest ``503 {"error": "snapshot
  unavailable"}`` instead of a blank 200.
- Everything else — the static frontend under ``web/``.

The layering contract (docs/architecture.md): data/ -> server/ -> web/;
the frontend talks to this process only via the JSON API, and this process
never writes anything.
"""

from __future__ import annotations

import json
import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT_PATH = REPO_ROOT / "data" / "sample_snapshot.json"
WEB_ROOT = REPO_ROOT / "web"

API_SNAPSHOT = "/api/snapshot"


class MineverseHandler(SimpleHTTPRequestHandler):
    """Static-file handler with the one JSON API route bolted on."""

    # Injected by make_server via functools.partial.
    snapshot_path: Path = SNAPSHOT_PATH

    def __init__(self, *args, snapshot_path: Path | None = None, **kwargs):
        if snapshot_path is not None:
            self.snapshot_path = snapshot_path
        super().__init__(*args, **kwargs)

    def do_GET(self):  # noqa: N802 (http.server API name)
        if self.path.split("?", 1)[0] == API_SNAPSHOT:
            self._serve_snapshot()
        elif self.path.startswith("/api/"):
            self._send_json(404, {"error": "unknown API route"})
        else:
            super().do_GET()

    def _serve_snapshot(self) -> None:
        try:
            payload = self.snapshot_path.read_bytes()
            json.loads(payload)  # never serve a corrupt snapshot as a 200
        except (OSError, ValueError):
            self._send_json(503, {"error": "snapshot unavailable"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def _send_json(self, status: int, body: dict) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        pass  # keep test output clean; stage 1 needs no access log


def make_server(
    host: str = "127.0.0.1",
    port: int = 0,
    *,
    snapshot_path: Path = SNAPSHOT_PATH,
    web_root: Path = WEB_ROOT,
) -> ThreadingHTTPServer:
    """Build (but don't start) the server — port 0 picks a free port."""
    handler = partial(
        MineverseHandler,
        directory=str(web_root),
        snapshot_path=snapshot_path,
    )
    return ThreadingHTTPServer((host, port), handler)


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))
    server = make_server(port=port)
    host, bound_port = server.server_address[:2]
    print(f"mineverse walking skeleton on http://{host}:{bound_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
