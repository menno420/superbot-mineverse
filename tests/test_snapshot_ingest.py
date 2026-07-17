"""FLAG-1 snapshot-ingest RECEIVE endpoint (POST /api/snapshot/ingest).

The receive half of the bot→web READ relay: superbot's pusher (#2058)
POSTs the v1 snapshot every ~60 s, HMAC-signed under the repo's ONE
canonical scheme (server/actions.py sign/verify). These tests pin the
full gauntlet through the real server on loopback, no env vars, no
secrets beyond test-local strings:

- transport auth: unsigned / bad key / wrong path / tampered body /
  stale timestamp are all 401 and NEVER persist a byte;
- fail closed: secret and/or persist path unset → honest 503, a signed
  or unsigned push alike is refused (no unsigned mode, no default
  secret, the committed sample is never a write target);
- content gauntlet: wrong verb 405, oversized 413, wrong content type
  415, malformed JSON 400, v1-contract violation 400 — none persist;
- the accept path: 200 {"status": "accepted"}, atomic whole-document
  persist, and the read routes serve the new document on their next
  per-request fresh read (round-trip through the FLAG-1 consume seam).
"""

import http.client
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from server import actions, ingest  # noqa: E402
from server.app import (  # noqa: E402
    API_SNAPSHOT_INGEST,
    SNAPSHOT_PATH,
    WEB_ROOT,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"
VALID_LIVE_FIXTURE = FIXTURES / "live_snapshot_valid.json"
WRONG_VERSION_FIXTURE = FIXTURES / "live_snapshot_wrong_version.json"
CORRUPT_FIXTURE = FIXTURES / "live_snapshot_corrupt.json"

TEST_SECRET = "ingest-test-secret"
VALID_BODY = VALID_LIVE_FIXTURE.read_bytes()
LIVE_GUILD_ID = "555000111222333444"


def post(url, body: bytes, headers=None):
    """POST returning (status, parsed_json_body) — HTTP errors included."""
    request = urllib.request.Request(
        url, data=body, headers=headers or {}, method="POST"
    )
    try:
        with urllib.request.urlopen(request) as res:
            return res.status, json.loads(res.read())
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read())


def signed_headers(body: bytes, *, secret=TEST_SECRET, path=API_SNAPSHOT_INGEST,
                   ts=None, signature=None, content_type="application/json"):
    ts = str(int(time.time())) if ts is None else ts
    sig = signature if signature is not None else actions.sign(
        secret, "POST", path, ts, body
    )
    return {
        "Content-Type": content_type,
        actions.HEADER_TIMESTAMP: ts,
        actions.HEADER_SIGNATURE: sig,
    }


@pytest.fixture()
def ingest_server(serve, tmp_path):
    """A configured ingest server → (base_url, persist_target_path).

    The persist target doubles as the read seam's snapshot_path — exactly
    the production wiring, where both come from MINING_SNAPSHOT_PATH —
    and starts ABSENT (read routes 503) so persistence is unmistakable.
    """
    target = tmp_path / "relay_snapshot.json"
    base = serve(
        snapshot_path=target,
        web_root=WEB_ROOT,
        ingest_config=ingest.IngestConfig(secret=TEST_SECRET, path=target),
    )
    return base, target


# --- the accept path ---------------------------------------------------------


def test_valid_signed_snapshot_is_accepted_and_persisted(ingest_server):
    base, target = ingest_server
    status, body = post(
        base + API_SNAPSHOT_INGEST, VALID_BODY, signed_headers(VALID_BODY)
    )
    assert (status, body) == (200, {"status": "accepted"})
    assert target.read_bytes() == VALID_BODY  # whole document, byte-exact


def test_accepted_snapshot_is_served_on_the_read_routes(ingest_server):
    # End-to-end through the FLAG-1 consume seam: before the push the read
    # routes answer the honest 503 (no relay document yet); after it they
    # serve the pushed snapshot on their per-request fresh read.
    base, _ = ingest_server
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        urllib.request.urlopen(base + "/api/snapshot")
    assert excinfo.value.code == 503
    status, _ = post(
        base + API_SNAPSHOT_INGEST, VALID_BODY, signed_headers(VALID_BODY)
    )
    assert status == 200
    with urllib.request.urlopen(base + "/api/snapshot") as res:
        assert res.status == 200
        assert json.loads(res.read())["guild_id"] == LIVE_GUILD_ID
    with urllib.request.urlopen(base + "/api/views") as res:
        assert res.status == 200


def test_second_push_replaces_the_document_whole(ingest_server):
    # Last-write-wins, replaced whole (contract § Atomicity) — the second
    # accepted document fully supersedes the first.
    base, target = ingest_server
    post(base + API_SNAPSHOT_INGEST, VALID_BODY, signed_headers(VALID_BODY))
    second = json.loads(VALID_BODY)
    second["miners"] = []
    second_body = json.dumps(second).encode("utf-8")
    status, _ = post(
        base + API_SNAPSHOT_INGEST, second_body, signed_headers(second_body)
    )
    assert status == 200
    assert target.read_bytes() == second_body


# --- freshness gate: generated_at-monotonic (replay hardening) ---------------

# VALID_BODY carries generated_at "2026-07-13T02:30:00Z"; these bracket it.
NEWER_GENERATED_AT = "2026-07-13T03:00:00Z"
OLDER_GENERATED_AT = "2026-07-13T02:00:00Z"
EQUAL_GENERATED_AT = "2026-07-13T02:30:00Z"


def body_with_generated_at(iso: str, **overrides) -> bytes:
    """VALID_BODY re-stamped with generated_at ``iso`` (plus any overrides)."""
    doc = json.loads(VALID_BODY)
    doc["generated_at"] = iso
    doc.update(overrides)
    return json.dumps(doc).encode("utf-8")


def test_newer_generated_at_replaces_the_live_snapshot(ingest_server):
    base, target = ingest_server
    post(base + API_SNAPSHOT_INGEST, VALID_BODY, signed_headers(VALID_BODY))
    newer = body_with_generated_at(NEWER_GENERATED_AT)
    status, body = post(base + API_SNAPSHOT_INGEST, newer, signed_headers(newer))
    assert (status, body) == (200, {"status": "accepted"})
    assert target.read_bytes() == newer


def test_strictly_older_generated_at_is_409_and_file_byte_unchanged(ingest_server):
    base, target = ingest_server
    post(base + API_SNAPSHOT_INGEST, VALID_BODY, signed_headers(VALID_BODY))
    before = target.read_bytes()
    older = body_with_generated_at(OLDER_GENERATED_AT)
    status, body = post(base + API_SNAPSHOT_INGEST, older, signed_headers(older))
    assert status == 409
    assert body == {
        "error": "stale_snapshot",
        "detail": "generated_at older than current",
    }
    assert target.read_bytes() == before  # rejected push is byte-for-byte inert


def test_equal_generated_at_is_idempotent_accept(ingest_server):
    # A replay of the "current instant" (equal generated_at) is accepted, not
    # gated — the monotone frontier is strict-older, so equal advances-in-place.
    base, target = ingest_server
    post(base + API_SNAPSHOT_INGEST, VALID_BODY, signed_headers(VALID_BODY))
    equal = body_with_generated_at(EQUAL_GENERATED_AT, miners=[])
    status, body = post(base + API_SNAPSHOT_INGEST, equal, signed_headers(equal))
    assert (status, body) == (200, {"status": "accepted"})
    assert target.read_bytes() == equal


def test_first_ingest_is_accepted_with_no_current_snapshot(ingest_server):
    # No current document to gate against → the gate never blocks the first push.
    base, target = ingest_server
    assert not target.exists()
    status, body = post(
        base + API_SNAPSHOT_INGEST, VALID_BODY, signed_headers(VALID_BODY)
    )
    assert (status, body) == (200, {"status": "accepted"})
    assert target.read_bytes() == VALID_BODY


def test_corrupt_current_file_never_blocks_a_valid_newer_push(ingest_server):
    # An unparseable current snapshot yields no comparable instant, so a valid
    # signed push must still land (the relay never wedges on a corrupt file).
    base, target = ingest_server
    target.write_bytes(b"{ not json at all")
    status, body = post(
        base + API_SNAPSHOT_INGEST, VALID_BODY, signed_headers(VALID_BODY)
    )
    assert (status, body) == (200, {"status": "accepted"})
    assert target.read_bytes() == VALID_BODY


# --- transport auth: 401, nothing persisted ----------------------------------


def test_unsigned_push_is_401_and_never_persisted(ingest_server):
    base, target = ingest_server
    status, body = post(
        base + API_SNAPSHOT_INGEST,
        VALID_BODY,
        {"Content-Type": "application/json"},
    )
    assert status == 401
    assert body["error"] == "invalid_signature"
    assert not target.exists()


@pytest.mark.parametrize(
    "headers_kwargs, label",
    [
        ({"secret": "wrong-secret"}, "wrong key"),
        ({"path": "/api/action"}, "signature bound to another path"),
        ({"signature": "deadbeef" * 8}, "garbage signature"),
    ],
)
def test_bad_signatures_are_401_and_never_persisted(
    ingest_server, headers_kwargs, label
):
    base, target = ingest_server
    status, body = post(
        base + API_SNAPSHOT_INGEST,
        VALID_BODY,
        signed_headers(VALID_BODY, **headers_kwargs),
    )
    assert status == 401, label
    assert body["error"] == "invalid_signature"
    assert not target.exists()


def test_tampered_body_fails_the_signature(ingest_server):
    # Sign one body, send another — the body hash is inside the signed string.
    base, target = ingest_server
    headers = signed_headers(VALID_BODY)
    tampered = VALID_BODY.replace(LIVE_GUILD_ID.encode(), b"999999999999999999")
    status, body = post(base + API_SNAPSHOT_INGEST, tampered, headers)
    assert status == 401
    assert body["error"] == "invalid_signature"
    assert not target.exists()


def test_stale_timestamp_is_401_and_never_persisted(ingest_server):
    base, target = ingest_server
    stale = str(int(time.time()) - actions.SKEW_SECONDS - 60)
    status, body = post(
        base + API_SNAPSHOT_INGEST, VALID_BODY, signed_headers(VALID_BODY, ts=stale)
    )
    assert status == 401
    assert body["error"] == "stale_timestamp"
    assert not target.exists()


# --- fail closed: unconfigured is a refusal, never an acceptance -------------


@pytest.mark.parametrize(
    "config, label",
    [
        (lambda tmp: ingest.IngestConfig(secret=None, path=tmp / "x.json"), "secret unset"),
        (lambda tmp: ingest.IngestConfig(secret=TEST_SECRET, path=None), "path unset"),
        (lambda tmp: ingest.IngestConfig(secret=None, path=None), "both unset"),
    ],
)
def test_unconfigured_ingest_fails_closed_even_for_a_signed_push(
    serve, tmp_path, config, label
):
    base = serve(
        snapshot_path=SNAPSHOT_PATH,
        web_root=WEB_ROOT,
        ingest_config=config(tmp_path),
    )
    status, body = post(
        base + API_SNAPSHOT_INGEST, VALID_BODY, signed_headers(VALID_BODY)
    )
    assert status == 503, label
    assert body["error"] == "snapshot ingest not configured"
    assert not (tmp_path / "x.json").exists()


def test_env_default_is_fail_closed(serve, monkeypatch):
    # The from_env default (no explicit ingest_config, relay env vars unset):
    # the endpoint exists but refuses — and the committed sample, which IS the
    # default snapshot_path, is never a write target.
    monkeypatch.delenv(ingest.ENV_INGEST_SECRET, raising=False)
    monkeypatch.delenv(ingest.ENV_SNAPSHOT_PATH, raising=False)
    before = SNAPSHOT_PATH.read_bytes()
    base = serve(web_root=WEB_ROOT)
    status, body = post(
        base + API_SNAPSHOT_INGEST, VALID_BODY, signed_headers(VALID_BODY)
    )
    assert status == 503
    assert body["error"] == "snapshot ingest not configured"
    assert SNAPSHOT_PATH.read_bytes() == before


def test_env_configured_ingest_accepts(serve, monkeypatch, tmp_path):
    # The exact main() resolution path: both relay env vars set, no explicit
    # ingest_config or snapshot_path arguments anywhere.
    target = tmp_path / "relay_snapshot.json"
    monkeypatch.setenv(ingest.ENV_INGEST_SECRET, TEST_SECRET)
    monkeypatch.setenv(ingest.ENV_SNAPSHOT_PATH, str(target))
    base = serve(web_root=WEB_ROOT)
    status, _ = post(
        base + API_SNAPSHOT_INGEST, VALID_BODY, signed_headers(VALID_BODY)
    )
    assert status == 200
    assert target.read_bytes() == VALID_BODY
    with urllib.request.urlopen(base + "/api/snapshot") as res:
        assert json.loads(res.read())["guild_id"] == LIVE_GUILD_ID


# --- content gauntlet: signed but unacceptable -------------------------------


def test_schema_invalid_snapshot_is_400_and_never_persisted(ingest_server):
    base, target = ingest_server
    body_bytes = WRONG_VERSION_FIXTURE.read_bytes()  # valid JSON, violates v1
    status, body = post(
        base + API_SNAPSHOT_INGEST, body_bytes, signed_headers(body_bytes)
    )
    assert status == 400
    assert body["error"] == "snapshot failed v1 validation"
    assert not target.exists()


def test_malformed_json_is_400_and_never_persisted(ingest_server):
    base, target = ingest_server
    body_bytes = CORRUPT_FIXTURE.read_bytes()  # signed correctly, not JSON
    status, body = post(
        base + API_SNAPSHOT_INGEST, body_bytes, signed_headers(body_bytes)
    )
    assert status == 400
    assert body["error"] == "snapshot is not valid JSON"
    assert not target.exists()


def test_wrong_content_type_is_415(ingest_server):
    base, target = ingest_server
    status, body = post(
        base + API_SNAPSHOT_INGEST,
        VALID_BODY,
        signed_headers(VALID_BODY, content_type="text/plain"),
    )
    assert status == 415
    assert not target.exists()


def test_oversized_body_is_413_before_auth(ingest_server):
    # The size check runs BEFORE the body is read (or verified), so the 413
    # arrives while the oversized body is still unsent — a raw http.client
    # round-trip reads it without pushing the megabyte through the socket.
    base, target = ingest_server
    host, port = urllib.parse.urlsplit(base).netloc.split(":")
    connection = http.client.HTTPConnection(host, int(port), timeout=5)
    try:
        connection.putrequest("POST", API_SNAPSHOT_INGEST)
        connection.putheader("Content-Type", "application/json")
        connection.putheader(
            "Content-Length", str(ingest.MAX_SNAPSHOT_BODY_BYTES + 1)
        )
        connection.endheaders()
        connection.send(b"{")  # a first byte, never the rest
        response = connection.getresponse()
        assert response.status == 413
        assert json.loads(response.read())["error"] == "snapshot too large"
    finally:
        connection.close()
    assert not target.exists()


def test_missing_body_is_400(ingest_server):
    base, _ = ingest_server
    status, body = post(
        base + API_SNAPSHOT_INGEST, b"", {"Content-Type": "application/json"}
    )
    assert status == 400
    assert body["error"] == "invalid content length"


# --- verbs and routes ---------------------------------------------------------


def test_get_on_the_ingest_route_is_405_allow_post(ingest_server):
    base, _ = ingest_server
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        urllib.request.urlopen(base + API_SNAPSHOT_INGEST)
    assert excinfo.value.code == 405
    assert excinfo.value.headers["Allow"] == "POST"


def test_put_on_the_ingest_route_is_405_allow_post(ingest_server):
    base, _ = ingest_server
    request = urllib.request.Request(
        base + API_SNAPSHOT_INGEST, data=VALID_BODY, method="PUT"
    )
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        urllib.request.urlopen(request)
    assert excinfo.value.code == 405
    assert excinfo.value.headers["Allow"] == "POST"


# --- units: config + persistence ---------------------------------------------


def test_ingest_config_from_env_requires_both_vars(tmp_path):
    assert not ingest.IngestConfig.from_env({}).configured
    assert not ingest.IngestConfig.from_env(
        {ingest.ENV_INGEST_SECRET: "s"}
    ).configured
    assert not ingest.IngestConfig.from_env(
        {ingest.ENV_SNAPSHOT_PATH: str(tmp_path / "s.json")}
    ).configured
    # Empty string counts as UNSET (the repo-wide `or None` convention).
    assert not ingest.IngestConfig.from_env(
        {ingest.ENV_INGEST_SECRET: "", ingest.ENV_SNAPSHOT_PATH: ""}
    ).configured
    config = ingest.IngestConfig.from_env(
        {
            ingest.ENV_INGEST_SECRET: "s",
            ingest.ENV_SNAPSHOT_PATH: str(tmp_path / "s.json"),
        }
    )
    assert config.configured
    assert config.path == tmp_path / "s.json"


def test_persist_snapshot_replaces_whole_and_leaves_no_temp_files(tmp_path):
    target = tmp_path / "snapshot.json"
    ingest.persist_snapshot(target, b'{"first": 1}')
    assert target.read_bytes() == b'{"first": 1}'
    ingest.persist_snapshot(target, b'{"second": 2}')
    assert target.read_bytes() == b'{"second": 2}'
    assert [p.name for p in tmp_path.iterdir()] == ["snapshot.json"]


def test_persist_snapshot_missing_directory_raises_oserror(tmp_path):
    # The parent directory is host-provisioned; persist never mkdirs.
    with pytest.raises(OSError):
        ingest.persist_snapshot(tmp_path / "no-such-dir" / "s.json", b"{}")
    assert not (tmp_path / "no-such-dir").exists()
