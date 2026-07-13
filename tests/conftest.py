"""Shared fixtures for the served-bytes web suites (tests/test_web_*.py).

Six web test modules pin the served frontend the same way: one real
server per module, substring asserts on the served files. The identical
fixture stack they each carried — module-scoped ``base_url`` over
``make_server``, the ``fetch_text`` helper and the ``html``/``js``/``css``
text fixtures — lives here once instead (recorded 💡 from
.sessions/2026-07-12-webaudio-cave-toggle.md).

Scope is deliberately ``module``, not ``session``: each web module still
gets its OWN server, exactly as before the move — same isolation, same
server count, zero behavior change. Module-specific fixtures
(``not_found_page`` in test_web_fun.py, ``seasonal_js_block`` in
test_web_seasonal.py) stay in their modules.

The API/auth suites build servers with per-test kwargs instead; their
shared ``serve`` fixture below wraps the importable
``tests/_server_helpers.serve_factory`` context manager (recorded 💡
from .sessions/2026-07-13-test-infra-dedupe.md). One divergent variant
stays module-local: test_server_robustness.py's ``serve`` returns a raw
``(host, port)`` tuple, not a URL, and deliberately overrides the
fixture defined here.
"""

import sys
import urllib.request
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from server.app import make_server  # noqa: E402
from tests._server_helpers import run_server, serve_factory  # noqa: E402


@pytest.fixture()
def serve():
    """Kwargs-taking ``start(**make_server kwargs) -> base URL`` factory.

    Every server started through the factory is shut down after the
    test. Per-test scope, exactly like the five per-module copies this
    replaces.
    """
    with serve_factory() as start:
        yield start


@pytest.fixture(scope="module")
def base_url():
    """One real server for the whole module — these are read-only GETs."""
    server = make_server(port=0)
    with run_server(server):
        host, port = server.server_address[:2]
        yield f"http://{host}:{port}"


def fetch_text(base_url, path):
    with urllib.request.urlopen(base_url + path) as res:
        assert res.status == 200
        return res.read().decode("utf-8")


@pytest.fixture(scope="module")
def html(base_url):
    return fetch_text(base_url, "/")


@pytest.fixture(scope="module")
def js(base_url):
    return fetch_text(base_url, "/app.js")


@pytest.fixture(scope="module")
def css(base_url):
    return fetch_text(base_url, "/style.css")
