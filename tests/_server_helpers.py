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
def run_server(server):
    """Own the thread lifecycle of an ALREADY-CONSTRUCTED server.

    Starts ``server.serve_forever`` in a daemon thread; on exit, tears
    down in the suites' canonical order — ``shutdown()`` →
    ``server_close()`` → ``join(timeout=5)``. Construction (and with it
    the yield shape: base URL, ``(state, url)``, ``(host, port)``…)
    stays at the call site; only the lifecycle lives here (recorded 💡
    from ``.sessions/2026-07-13-serve-helper-dedupe.md``).

    Single-server sites only. The factory-style fixtures that start N
    servers and tear them down first-started-first (``serve_factory``
    below, test_actions.py's ``fake_executor``,
    test_server_robustness.py's ``serve``) keep their list loops:
    stacking N of these contexts would flip that multi-server teardown
    to last-started-first.
    """
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


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
