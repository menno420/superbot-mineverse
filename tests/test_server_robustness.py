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
    """Start the real server on an ephemeral port; yield (host, port).

    Deliberately module-local, overriding the conftest ``serve``: the
    raw http.client round-trips here need the ``(host, port)`` tuple,
    not the base-URL string the shared factory returns.
    """
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


def test_structurally_invalid_snapshot_is_refused_at_ingestion(serve, tmp_path):
    # A valid JSON object that violates the v1 READ contract (here: the whole
    # envelope is missing and equipment is a non-mapping) is now refused at
    # INGESTION with an honest 503 by the runtime validator, BEFORE the view
    # shaper ever runs — so the frontend never receives shaped-but-corrupt data.
    # (Previously this reached views.build_views and drew a 500; the ingestion
    # guard is the earlier, stronger bite. The build_views try/except in
    # _serve_views is kept as defense-in-depth for any structurally-valid but
    # shaper-hostile payload.)
    bad = tmp_path / "malformed.json"
    bad.write_text(json.dumps(
        {"miners": [{"equipment": "not-a-mapping", "gear_wear": 3}]}))
    addr = serve(snapshot_path=bad, web_root=WEB_ROOT)
    status, headers, body = request(addr, "GET", "/api/views")
    assert status == 503
    assert headers["content-type"].startswith("application/json")
    assert json.loads(body) == {"error": "snapshot unavailable"}


def test_missing_snapshot_stays_an_honest_503_on_views(serve, tmp_path):
    addr = serve(snapshot_path=tmp_path / "gone.json", web_root=WEB_ROOT)
    status, _, body = request(addr, "GET", "/api/views")
    assert status == 503
    assert json.loads(body) == {"error": "snapshot unavailable"}


# --- cave-art 404 page (unknown non-API GET paths only) ----------------------


def test_unknown_static_path_serves_the_cave_404_page(serve):
    status, headers, body = request(serve(), "GET", "/no/such/tunnel")
    assert status == 404
    assert headers["content-type"] == "text/html; charset=utf-8"
    text = body.decode("utf-8")
    assert "you dug too deep" in text  # the cave-art page, not the stock one
    assert "404" in text
    assert 'href="/"' in text  # the way back up is a real link


def test_head_on_unknown_static_path_is_404_with_no_body(serve):
    status, headers, body = request(serve(), "HEAD", "/no/such/tunnel")
    assert status == 404
    assert headers["content-type"] == "text/html; charset=utf-8"
    assert body == b""


def test_api_json_404_is_untouched_by_the_404_page(serve):
    # The /api/* error contract stays byte-identical: JSON body, JSON
    # content type, no HTML — on every method (405s pinned above).
    for method in ("GET", "POST", "PUT", "DELETE", "PATCH"):
        status, headers, body = request(serve(), method, "/api/unknown")
        assert status == 404, method
        assert headers["content-type"] == "application/json; charset=utf-8"
        assert json.loads(body) == {"error": "unknown API route"}, method


def test_missing_404_page_falls_back_to_the_stock_error(serve, tmp_path):
    # An empty web root has no 404.html — the server answers the stock
    # http.server error page honestly instead of a blank or a crash.
    addr = serve(web_root=tmp_path)
    status, headers, body = request(addr, "GET", "/nope")
    assert status == 404
    assert headers["content-type"].startswith("text/html")
    assert b"404" in body


# --- X-Content-Type-Options: nosniff on EVERY response ----------------------
# One end_headers() choke point, so the header rides API JSON, static files,
# 304s, and error pages alike.


def test_nosniff_on_200_json_and_static(serve):
    addr = serve()
    for path in ("/api/snapshot", "/"):
        _, headers, _ = request(addr, "GET", path)
        assert headers["x-content-type-options"] == "nosniff", path


def test_nosniff_on_a_304(serve):
    addr = serve()
    _, headers, _ = request(addr, "GET", "/api/snapshot")
    etag = headers["etag"]
    status, headers304, _ = request(
        addr, "GET", "/api/snapshot", headers={"If-None-Match": etag})
    assert status == 304
    assert headers304["x-content-type-options"] == "nosniff"


def test_nosniff_on_404_api_and_static(serve):
    addr = serve()
    for path in ("/api/nope", "/no-such-page.html"):
        status, headers, _ = request(addr, "GET", path)
        assert status == 404, path
        assert headers["x-content-type-options"] == "nosniff", path


def test_nosniff_on_a_405(serve):
    status, headers, _ = request(serve(), "POST", "/")
    assert status == 405
    assert headers["x-content-type-options"] == "nosniff"


def test_nosniff_on_a_503(serve, tmp_path):
    # A non-existent snapshot_path draws the honest 503 — nosniff rides it too.
    addr = serve(snapshot_path=tmp_path / "gone.json", web_root=WEB_ROOT)
    status, headers, _ = request(addr, "GET", "/api/snapshot")
    assert status == 503
    assert headers["x-content-type-options"] == "nosniff"


# --- HEAD works on the read API routes: GET headers, empty body -------------


@pytest.mark.parametrize("path", ["/api/snapshot", "/api/views", "/api/me"])
def test_head_on_read_api_routes_mirrors_get_headers_without_body(serve, path):
    addr = serve()
    gstatus, gheaders, gbody = request(addr, "GET", path)
    hstatus, hheaders, hbody = request(addr, "HEAD", path)
    assert gstatus == 200 and hstatus == 200
    # Header-only: all headers (incl. Content-Length) match GET, body is empty.
    assert hbody == b""
    ctype = hheaders["content-type"]
    assert ctype.startswith("application/json")
    assert "charset=utf-8" in ctype
    assert hheaders["content-length"] == str(len(gbody))
    # Every header identical to GET (Date is clock-dependent — drop it).
    gheaders.pop("date", None)
    hheaders.pop("date", None)
    assert hheaders == gheaders


@pytest.mark.parametrize("path", ["/api/snapshot", "/api/views"])
def test_head_on_cacheable_read_routes_carries_the_etag(serve, path):
    # The committed-data routes ETag; HEAD must expose it (and content-length)
    # so a client can revalidate without ever fetching a body.
    status, headers, body = request(serve(), "HEAD", path)
    assert status == 200
    assert headers["etag"].startswith('"') and headers["etag"].endswith('"')
    assert headers["content-length"] != "0"
    assert body == b""


def test_head_on_static_root_still_works(serve):
    status, headers, body = request(serve(), "HEAD", "/")
    assert status == 200
    assert headers["content-type"].startswith("text/html")
    assert body == b""


def test_head_on_unknown_path_stays_a_404_with_no_body(serve):
    # Extends the /no/such/tunnel regression: the inherited static HEAD still
    # 404s unknown non-API paths, header-only.
    status, headers, body = request(serve(), "HEAD", "/no/such/path")
    assert status == 404
    assert body == b""


# --- OPTIONS: 204 + honest Allow per route class ----------------------------


@pytest.mark.parametrize("path", ["/api/snapshot", "/api/views", "/api/me"])
def test_options_on_read_routes_is_204_allowing_get_head_options(serve, path):
    status, headers, body = request(serve(), "OPTIONS", path)
    assert status == 204
    assert headers["allow"] == "GET, HEAD, OPTIONS"
    assert body == b""


@pytest.mark.parametrize("path", ["/api/action", "/api/snapshot/ingest"])
def test_options_on_post_routes_is_204_allowing_post_options(serve, path):
    status, headers, body = request(serve(), "OPTIONS", path)
    assert status == 204
    assert headers["allow"] == "POST, OPTIONS"
    assert body == b""


def test_options_on_unknown_api_route_is_json_404(serve):
    status, headers, body = request(serve(), "OPTIONS", "/api/nope")
    assert status == 404
    assert headers["content-type"] == "application/json; charset=utf-8"
    assert json.loads(body) == {"error": "unknown API route"}
