"""HTTP robustness tests for the stdlib server (server/app.py).

Pins the polish layer around the read routes: charset on every
Content-Type, content-hash ETag + If-None-Match -> 304 conditional
caching on the committed-data endpoints, honest 404/405 handling
(JSON error shape on /api/*, Allow header on 405), and the
malformed-snapshot guard (5xx with a clear body — never a crash, never
a bogus 200 relaying corrupt data).
"""

import http.client
import json
import sys
import threading
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from server.app import WEB_ROOT, make_server  # noqa: E402


@pytest.fixture()
def serve():
    """Start the real server on an ephemeral port; yield (host, port)."""
    servers = []

    def _start(**kwargs):
        server = make_server(port=0, **kwargs)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        servers.append((server, thread))
        return server.server_address[:2]

    yield _start
    for server, thread in servers:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def request(addr, method, path, headers=None):
    """One raw round-trip — http.client so 304/405 are plain responses."""
    conn = http.client.HTTPConnection(*addr, timeout=10)
    try:
        conn.request(method, path, headers=headers or {})
        res = conn.getresponse()
        # HTTP header names are case-insensitive (http.server emits
        # "Content-type" for static files) — normalize keys to lowercase.
        headers = {name.lower(): value for name, value in res.getheaders()}
        return res.status, headers, res.read()
    finally:
        conn.close()


# --- Content-Type always carries a charset ----------------------------------


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/", "text/html"),
        ("/index.html", "text/html"),
        ("/style.css", "text/css"),
        ("/app.js", ("application/javascript", "text/javascript")),
        ("/api/snapshot", "application/json"),
        ("/api/views", "application/json"),
        ("/api/me", "application/json"),
    ],
)
def test_every_content_type_declares_utf8(serve, path, expected):
    status, headers, _ = request(serve(), "GET", path)
    assert status == 200
    ctype = headers["content-type"]
    if isinstance(expected, str):
        expected = (expected,)
    assert any(ctype.startswith(e) for e in expected), ctype
    assert "charset=utf-8" in ctype, f"{path} served without a charset: {ctype}"


def test_error_bodies_declare_utf8_too(serve):
    status, headers, _ = request(serve(), "GET", "/api/nope")
    assert status == 404
    assert "charset=utf-8" in headers["content-type"]


# --- conditional caching: content-hash ETag + If-None-Match -> 304 ----------


@pytest.mark.parametrize("path", ["/api/snapshot", "/api/views"])
def test_read_endpoints_ship_a_stable_etag(serve, path):
    addr = serve()
    status, headers, body = request(addr, "GET", path)
    assert status == 200
    etag = headers["etag"]
    assert etag.startswith('"') and etag.endswith('"')
    assert headers["cache-control"] == "no-cache"  # revalidate, don't refetch
    # Same committed bytes -> same tag on the next request.
    _, headers2, _ = request(addr, "GET", path)
    assert headers2["etag"] == etag


@pytest.mark.parametrize("path", ["/api/snapshot", "/api/views"])
def test_if_none_match_answers_304_with_no_body(serve, path):
    addr = serve()
    _, headers, _ = request(addr, "GET", path)
    etag = headers["etag"]
    status, headers304, body = request(
        addr, "GET", path, headers={"If-None-Match": etag})
    assert status == 304
    assert body == b""
    assert headers304["etag"] == etag


def test_if_none_match_miss_still_serves_200(serve):
    status, _, body = request(
        serve(), "GET", "/api/snapshot", headers={"If-None-Match": '"stale"'})
    assert status == 200
    assert json.loads(body)["schema_version"] == "1"


def test_if_none_match_handles_weak_and_wildcard_forms(serve):
    addr = serve()
    _, headers, _ = request(addr, "GET", "/api/views")
    etag = headers["etag"]
    for header in (f"W/{etag}", f'"other", {etag}', "*"):
        status, _, _ = request(
            addr, "GET", "/api/views", headers={"If-None-Match": header})
        assert status == 304, f"If-None-Match: {header} should hit"


# --- 404: correct status + honest body (JSON shape on /api/*) ---------------


def test_unknown_api_route_is_json_404_on_every_method(serve):
    addr = serve()
    for method in ("GET", "POST", "PUT", "DELETE", "PATCH"):
        status, headers, body = request(addr, method, "/api/nope")
        assert status == 404, method
        assert headers["content-type"].startswith("application/json"), method
        assert json.loads(body) == {"error": "unknown API route"}, method


def test_missing_static_file_is_a_plain_404(serve):
    status, headers, body = request(serve(), "GET", "/no-such-page.html")
    assert status == 404
    assert headers["content-type"].startswith("text/html")
    assert b"404" in body  # honest error page, not an empty 200


# --- 405: wrong verb on a real route, with an Allow header ------------------


@pytest.mark.parametrize("path", ["/api/snapshot", "/api/views", "/api/me"])
@pytest.mark.parametrize("method", ["POST", "PUT", "DELETE", "PATCH"])
def test_write_verbs_on_read_api_routes_are_405(serve, method, path):
    status, headers, body = request(serve(), method, path)
    assert status == 405
    assert headers["allow"] == "GET, HEAD"
    assert json.loads(body) == {"error": "method not allowed"}


@pytest.mark.parametrize("method", ["GET", "PUT", "DELETE", "PATCH"])
def test_non_post_on_action_route_is_405_allowing_post(serve, method):
    status, headers, body = request(serve(), method, "/api/action")
    assert status == 405
    assert headers["allow"] == "POST"
    assert json.loads(body) == {"error": "method not allowed"}


def test_post_to_static_path_is_405_allowing_get(serve):
    status, headers, _ = request(serve(), "POST", "/")
    assert status == 405
    assert headers["allow"] == "GET, HEAD"


# --- malformed snapshot: honest 5xx, never a crash or a bogus 200 -----------


def test_non_object_snapshot_is_503_on_both_read_routes(serve, tmp_path):
    # Valid JSON, but not the contract's object envelope — corrupt data.
    bogus = tmp_path / "list.json"
    bogus.write_text('[1, 2, 3]')
    addr = serve(snapshot_path=bogus, web_root=WEB_ROOT)
    for path in ("/api/snapshot", "/api/views"):
        status, _, body = request(addr, "GET", path)
        assert status == 503, path
        assert json.loads(body) == {"error": "snapshot unavailable"}, path


def test_snapshot_the_shaper_chokes_on_is_a_clean_500(serve, tmp_path):
    # Valid JSON object, but shaped so views.build_views raises
    # (equipment as a string defeats the gear panel's .get calls).
    # Before the guard this crashed the request thread — the client saw
    # a dropped connection instead of a status. Never a bogus 200.
    bad = tmp_path / "malformed.json"
    bad.write_text(json.dumps(
        {"miners": [{"equipment": "not-a-mapping", "gear_wear": 3}]}))
    addr = serve(snapshot_path=bad, web_root=WEB_ROOT)
    status, headers, body = request(addr, "GET", "/api/views")
    assert status == 500
    assert headers["content-type"].startswith("application/json")
    assert json.loads(body) == {"error": "snapshot malformed"}


def test_missing_snapshot_stays_an_honest_503_on_views(serve, tmp_path):
    addr = serve(snapshot_path=tmp_path / "gone.json", web_root=WEB_ROOT)
    status, _, body = request(addr, "GET", "/api/views")
    assert status == 503
    assert json.loads(body) == {"error": "snapshot unavailable"}
