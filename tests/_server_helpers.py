"""Importable server-lifecycle helper for the API-style test suites.

Five non-web suites (test_actions, test_api, test_auth,
test_snapshot_validation, test_views) each carried a byte-identical
``serve`` fixture: a kwargs-taking ``_start(**make_server kwargs)``
factory returning a base URL, with every started server shut down on
teardown. The canonical copy lives here once as a plain context manager
(recorded 💡 from ``.sessions/2026-07-13-test-infra-dedupe.md``) — a
context manager rather than a fixture because conftest.py is
pytest-magic, not an import target; ``tests/conftest.py`` wraps this in
the shared ``serve`` fixture the suites consume.

The one divergent variant stays put: test_server_robustness.py's
``serve`` returns a raw ``(host, port)`` tuple for http.client
round-trips, not a URL — its module-local fixture deliberately
overrides the conftest one.
"""

import sys
import threading
from contextlib import contextmanager
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from server.app import make_server  # noqa: E402


@contextmanager
def serve_factory():
    """Yield a ``start(**make_server kwargs) -> base URL`` factory.

    Each call starts the real server on an ephemeral port in a daemon
    thread; every server started through the factory is shut down on
    context exit.
    """
    servers = []

    def _start(**kwargs):
        server = make_server(port=0, **kwargs)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        servers.append((server, thread))
        host, port = server.server_address[:2]
        return f"http://{host}:{port}"

    try:
        yield _start
    finally:
        for server, thread in servers:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
