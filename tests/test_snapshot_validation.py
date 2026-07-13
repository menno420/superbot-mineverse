"""Runtime snapshot validation at ingestion (stdlib-only, no jsonschema).

Two layers:

- UNIT: server/snapshot_validation.py accepts the committed sample and rejects
  contract violations — the same bites the CI jsonschema gate
  (tests/test_schema_gate.py) has, re-implemented stdlib-only for runtime use.
- HTTP: a snapshot that is valid JSON but violates the v1 READ contract is
  refused with an honest 503 on /api/snapshot and /api/views, instead of being
  served as 200. This exercises the future live bot→web relay at ingestion.
"""

import copy
import http.client
import json
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from server import snapshot_validation  # noqa: E402
from server.app import (  # noqa: E402
    ENV_SNAPSHOT_PATH,
    SNAPSHOT_PATH,
    WEB_ROOT,
    make_server,
    snapshot_path_from_env,
)

SAMPLE = json.loads(SNAPSHOT_PATH.read_text())

FIXTURES = Path(__file__).resolve().parent / "fixtures"
VALID_LIVE_FIXTURE = FIXTURES / "live_snapshot_valid.json"
WRONG_VERSION_FIXTURE = FIXTURES / "live_snapshot_wrong_version.json"
SCHEMA_VIOLATION_FIXTURE = FIXTURES / "live_snapshot_schema_violation.json"
CORRUPT_FIXTURE = FIXTURES / "live_snapshot_corrupt.json"

# The valid live fixture is deliberately DISTINCT from the committed sample so
# a test can tell which file actually got served.
LIVE_GUILD_ID = "555000111222333444"
assert LIVE_GUILD_ID != SAMPLE["guild_id"]


# --- unit: the stdlib validator ---------------------------------------------


def test_valid_sample_passes():
    # Returns the snapshot (does not raise) for the committed, conformant sample.
    assert snapshot_validation.validate_snapshot(copy.deepcopy(SAMPLE)) is not None


def test_non_object_root_rejected():
    for bad in ([], "x", 3, None):
        with pytest.raises(snapshot_validation.SnapshotInvalid):
            snapshot_validation.validate_snapshot(bad)


def test_wrong_version_pin_rejected():
    broken = copy.deepcopy(SAMPLE)
    broken["schema_version"] = "2"
    with pytest.raises(snapshot_validation.SnapshotInvalid):
        snapshot_validation.validate_snapshot(broken)


def test_missing_envelope_field_rejected():
    broken = copy.deepcopy(SAMPLE)
    del broken["generated_at"]
    with pytest.raises(snapshot_validation.SnapshotInvalid):
        snapshot_validation.validate_snapshot(broken)


def test_undeclared_envelope_field_rejected():
    broken = copy.deepcopy(SAMPLE)
    broken["surprise"] = True
    with pytest.raises(snapshot_validation.SnapshotInvalid):
        snapshot_validation.validate_snapshot(broken)


def test_numeric_snowflake_rejected():
    broken = copy.deepcopy(SAMPLE)
    broken["guild_id"] = 987654321098765432
    with pytest.raises(snapshot_validation.SnapshotInvalid):
        snapshot_validation.validate_snapshot(broken)


def test_missing_required_miner_field_rejected():
    broken = copy.deepcopy(SAMPLE)
    del broken["miners"][0]["mining_inventory"]
    with pytest.raises(snapshot_validation.SnapshotInvalid):
        snapshot_validation.validate_snapshot(broken)


def test_unknown_equipment_slot_rejected():
    broken = copy.deepcopy(SAMPLE)
    broken["miners"][0]["equipment"]["hat"] = "party hat"
    with pytest.raises(snapshot_validation.SnapshotInvalid):
        snapshot_validation.validate_snapshot(broken)


def test_out_of_band_values_rejected():
    for field, value in (("depth", 4), ("vault_level", 7)):
        broken = copy.deepcopy(SAMPLE)
        broken["miners"][0][field] = value
        with pytest.raises(snapshot_validation.SnapshotInvalid):
            snapshot_validation.validate_snapshot(broken)
    broken = copy.deepcopy(SAMPLE)
    broken["miners"][0]["energy"]["current"] = 61  # oracle cap is 60
    with pytest.raises(snapshot_validation.SnapshotInvalid):
        snapshot_validation.validate_snapshot(broken)


def test_wrong_type_rejected():
    broken = copy.deepcopy(SAMPLE)
    broken["miners"] = "not a list"
    with pytest.raises(snapshot_validation.SnapshotInvalid):
        snapshot_validation.validate_snapshot(broken)


def test_dynamic_map_keys_allowed():
    # Item/skill/structure names are oracle-owned and open-ended — new names
    # must NOT trip the runtime check (parity with the CI gate).
    grown = copy.deepcopy(SAMPLE)
    miner = grown["miners"][0]
    miner["mining_inventory"]["unobtainium"] = 1
    miner["skills"]["spelunking"] = 1
    miner["structures"]["observatory"] = 1
    assert snapshot_validation.validate_snapshot(grown) is not None


def test_maxitems_violation_rejected():
    # ``biomes`` carries maxItems: 4 in the schema; a longer array must be
    # rejected at runtime (parity with the CI jsonschema gate). Regression for
    # the size/length keywords the interpreter used to silently ignore.
    for count in (5, 5000):
        broken = copy.deepcopy(SAMPLE)
        broken["biomes"] = ["surface"] * count
        with pytest.raises(snapshot_validation.SnapshotInvalid):
            snapshot_validation.validate_snapshot(broken)


def test_within_maxitems_allowed():
    ok = copy.deepcopy(SAMPLE)
    ok["biomes"] = ["surface", "caves", "depths", "core"]  # exactly maxItems: 4
    assert snapshot_validation.validate_snapshot(ok) is not None


def test_size_length_keywords_enforced_via_synthetic_schema():
    # The interpreter implements the full stdlib size/length family even though
    # the committed schema only exercises maxItems today.
    array_schema = {"type": "array", "minItems": 2, "maxItems": 3}
    assert snapshot_validation.validate_snapshot([1, 2], schema=array_schema) == [1, 2]
    for bad in ([1], [1, 2, 3, 4]):
        with pytest.raises(snapshot_validation.SnapshotInvalid):
            snapshot_validation.validate_snapshot(bad, schema=array_schema)

    string_schema = {"type": "string", "minLength": 2, "maxLength": 4}
    assert snapshot_validation.validate_snapshot("abc", schema=string_schema) == "abc"
    for bad in ("a", "abcde"):
        with pytest.raises(snapshot_validation.SnapshotInvalid):
            snapshot_validation.validate_snapshot(bad, schema=string_schema)

    object_schema = {"type": "object", "minProperties": 1, "maxProperties": 2}
    assert snapshot_validation.validate_snapshot({"a": 1}, schema=object_schema)
    for bad in ({}, {"a": 1, "b": 2, "c": 3}):
        with pytest.raises(snapshot_validation.SnapshotInvalid):
            snapshot_validation.validate_snapshot(bad, schema=object_schema)


def test_unimplemented_keyword_fails_loud(caplog):
    # A schema carrying a *validation* keyword the interpreter does not implement
    # must fail loud (invalid + a warning naming the keyword) rather than
    # silently pass — otherwise the runtime validator drifts from the schema.
    drifting = {"type": "integer", "multipleOf": 2}
    with caplog.at_level("WARNING", logger="server.snapshot_validation"):
        with pytest.raises(snapshot_validation.SnapshotInvalid) as excinfo:
            snapshot_validation.validate_snapshot(4, schema=drifting)
    assert "multipleOf" in str(excinfo.value)
    assert any("multipleOf" in rec.getMessage() for rec in caplog.records)


def test_noop_annotation_keywords_do_not_fail_loud():
    # Annotation / structural keywords with no runtime assertion effect must be
    # tolerated (the committed schema uses $schema/$id/title/description/format).
    annotated = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "x",
        "title": "t",
        "description": "d",
        "$comment": "c",
        "type": "object",
        "properties": {"generated_at": {"type": "string", "format": "date-time"}},
        "required": ["generated_at"],
    }
    assert snapshot_validation.validate_snapshot(
        {"generated_at": "2026-07-11T00:00:00Z"}, schema=annotated
    )


# --- HTTP: ingestion-time 503 ------------------------------------------------


@pytest.fixture()
def serve():
    servers = []

    def _start(**kwargs):
        server = make_server(port=0, **kwargs)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        servers.append((server, thread))
        host, port = server.server_address[:2]
        return f"http://{host}:{port}"

    yield _start
    for server, thread in servers:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def fetch(url):
    with urllib.request.urlopen(url) as res:
        return res.status, res.read()


def write_snapshot(tmp_path, snapshot):
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(snapshot))
    return path


def test_valid_snapshot_serves_200_on_both_read_routes(serve, tmp_path):
    base = serve(snapshot_path=write_snapshot(tmp_path, SAMPLE), web_root=WEB_ROOT)
    for route in ("/api/snapshot", "/api/views"):
        status, _ = fetch(base + route)
        assert status == 200, route


def test_invalid_snapshot_is_503_on_snapshot_route(serve, tmp_path):
    broken = copy.deepcopy(SAMPLE)
    broken["schema_version"] = "2"  # valid JSON, violates the v1 version pin
    base = serve(snapshot_path=write_snapshot(tmp_path, broken), web_root=WEB_ROOT)
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        fetch(base + "/api/snapshot")
    assert excinfo.value.code == 503
    assert json.loads(excinfo.value.read())["error"] == "snapshot unavailable"


def test_invalid_snapshot_is_503_on_views_route(serve, tmp_path):
    broken = copy.deepcopy(SAMPLE)
    del broken["miners"][0]["mining_inventory"]  # missing required miner field
    base = serve(snapshot_path=write_snapshot(tmp_path, broken), web_root=WEB_ROOT)
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        fetch(base + "/api/views")
    assert excinfo.value.code == 503


def test_out_of_band_snapshot_is_503(serve, tmp_path):
    broken = copy.deepcopy(SAMPLE)
    broken["miners"][0]["depth"] = 9  # oracle depth bands are 0-3
    base = serve(snapshot_path=write_snapshot(tmp_path, broken), web_root=WEB_ROOT)
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        fetch(base + "/api/snapshot")
    assert excinfo.value.code == 503


def test_maxitems_violation_is_503_at_http_layer(serve, tmp_path):
    # A snapshot violating a size keyword (biomes maxItems: 4) must be refused
    # with an honest 503, not served as 200. Regression: the runtime validator
    # used to ignore maxItems and pass this snapshot the CI gate rejects.
    broken = copy.deepcopy(SAMPLE)
    broken["biomes"] = ["surface"] * 5000
    base = serve(snapshot_path=write_snapshot(tmp_path, broken), web_root=WEB_ROOT)
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        fetch(base + "/api/snapshot")
    assert excinfo.value.code == 503
    assert json.loads(excinfo.value.read())["error"] == "snapshot unavailable"


# --- committed fixtures stay honest about what they claim to be --------------


def test_valid_live_fixture_conforms_to_v1():
    # Bot-shaped, distinct from the sample, and genuinely valid — both under
    # the runtime interpreter and (parity) the real jsonschema CI validator.
    snapshot = json.loads(VALID_LIVE_FIXTURE.read_text())
    assert snapshot["guild_id"] == LIVE_GUILD_ID
    assert snapshot != SAMPLE
    assert snapshot_validation.validate_snapshot(snapshot) is not None
    jsonschema = pytest.importorskip("jsonschema")
    jsonschema.Draft202012Validator(snapshot_validation.load_schema()).validate(
        snapshot
    )


@pytest.mark.parametrize(
    "fixture", [WRONG_VERSION_FIXTURE, SCHEMA_VIOLATION_FIXTURE]
)
def test_invalid_fixtures_are_valid_json_but_fail_v1(fixture):
    snapshot = json.loads(fixture.read_text())  # parses fine — the contract bites
    with pytest.raises(snapshot_validation.SnapshotInvalid):
        snapshot_validation.validate_snapshot(snapshot)


def test_corrupt_fixture_is_not_even_json():
    with pytest.raises(ValueError):
        json.loads(CORRUPT_FIXTURE.read_text())


# --- committed-schema cache: parsed once, explicit clear seam ----------------


def test_load_schema_is_cached_with_an_explicit_clear_seam(tmp_path):
    # The COMMITTED schema is parsed once (lru_cache) — the cache is on the
    # ruler, never on the snapshot being measured (the live-rewrite seam test
    # below pins that SNAPSHOT bytes are still re-read fresh per request).
    original_path = snapshot_validation.SCHEMA_PATH
    snapshot_validation.load_schema.cache_clear()
    try:
        first = snapshot_validation.load_schema()
        assert snapshot_validation.load_schema() is first  # cached, not re-parsed
        edited = tmp_path / "edited.schema.json"
        edited.write_text('{"type": "object"}')
        snapshot_validation.SCHEMA_PATH = edited
        # An edit is invisible until the explicit seam is used …
        assert snapshot_validation.load_schema() is first
        # … and cache_clear() genuinely picks the new file up.
        snapshot_validation.load_schema.cache_clear()
        assert snapshot_validation.load_schema() == {"type": "object"}
    finally:
        snapshot_validation.SCHEMA_PATH = original_path
        snapshot_validation.load_schema.cache_clear()


# --- env ingestion seam: MINING_SNAPSHOT_PATH (FLAG 1 consume side) ----------
#
# serve() without an explicit snapshot_path exercises make_server's default —
# the exact resolution main() relies on — so these are the main-path semantics.


def test_snapshot_path_from_env_defaults_to_the_committed_sample():
    assert snapshot_path_from_env({}) == SNAPSHOT_PATH
    # Empty string counts as UNSET, mirroring WriteConfig.from_env's `or None`.
    assert snapshot_path_from_env({ENV_SNAPSHOT_PATH: ""}) == SNAPSHOT_PATH


def test_snapshot_path_from_env_honours_the_var():
    assert snapshot_path_from_env(
        {ENV_SNAPSHOT_PATH: "/srv/relay/snapshot.json"}
    ) == Path("/srv/relay/snapshot.json")


def test_env_unset_serves_the_committed_sample(serve, monkeypatch):
    monkeypatch.delenv(ENV_SNAPSHOT_PATH, raising=False)
    base = serve()  # no explicit snapshot_path — make_server default
    status, body = fetch(base + "/api/snapshot")
    assert status == 200
    assert json.loads(body)["guild_id"] == SAMPLE["guild_id"]


def test_env_set_to_valid_fixture_is_served_on_both_read_routes(serve, monkeypatch):
    monkeypatch.setenv(ENV_SNAPSHOT_PATH, str(VALID_LIVE_FIXTURE))
    base = serve()
    status, body = fetch(base + "/api/snapshot")
    assert status == 200
    assert json.loads(body)["guild_id"] == LIVE_GUILD_ID  # the fixture, not the sample
    status, body = fetch(base + "/api/views")
    assert status == 200
    assert json.loads(body)["guild_id"] == LIVE_GUILD_ID


def test_env_set_to_missing_file_is_an_honest_503(serve, monkeypatch, tmp_path):
    # A live feed that never arrived must NOT silently fall back to sample data.
    monkeypatch.setenv(ENV_SNAPSHOT_PATH, str(tmp_path / "never-written.json"))
    base = serve()
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        fetch(base + "/api/snapshot")
    assert excinfo.value.code == 503
    assert json.loads(excinfo.value.read())["error"] == "snapshot unavailable"


@pytest.mark.parametrize(
    "fixture",
    [CORRUPT_FIXTURE, WRONG_VERSION_FIXTURE, SCHEMA_VIOLATION_FIXTURE],
    ids=["corrupt-json", "wrong-version", "schema-violation"],
)
def test_env_set_to_invalid_fixture_is_an_honest_503(serve, monkeypatch, fixture):
    monkeypatch.setenv(ENV_SNAPSHOT_PATH, str(fixture))
    base = serve()
    for route in ("/api/snapshot", "/api/views"):
        with pytest.raises(urllib.error.HTTPError) as excinfo:
            fetch(base + route)
        assert excinfo.value.code == 503, route
        assert json.loads(excinfo.value.read())["error"] == "snapshot unavailable"


def test_explicit_snapshot_path_argument_beats_the_env(serve, monkeypatch, tmp_path):
    # Tests (and any embedder) that pass snapshot_path explicitly must stay
    # immune to the host environment.
    monkeypatch.setenv(ENV_SNAPSHOT_PATH, str(VALID_LIVE_FIXTURE))
    explicit = write_snapshot(tmp_path, SAMPLE)
    base = serve(snapshot_path=explicit, web_root=WEB_ROOT)
    status, body = fetch(base + "/api/snapshot")
    assert status == 200
    assert json.loads(body)["guild_id"] == SAMPLE["guild_id"]


def test_live_fed_file_is_reread_fresh_on_every_request(serve, monkeypatch, tmp_path):
    # The relay overwrites its file between requests; each GET must see the
    # newest bytes — and a feed that turns invalid mid-flight must flip to the
    # honest 503, not keep serving a remembered last-good snapshot.
    live = tmp_path / "live.json"
    live.write_text(VALID_LIVE_FIXTURE.read_text())
    monkeypatch.setenv(ENV_SNAPSHOT_PATH, str(live))
    base = serve()
    status, body = fetch(base + "/api/snapshot")
    assert status == 200
    assert json.loads(body)["guild_id"] == LIVE_GUILD_ID
    live.write_text(json.dumps(SAMPLE))  # relay pushed a new snapshot
    status, body = fetch(base + "/api/snapshot")
    assert status == 200
    assert json.loads(body)["guild_id"] == SAMPLE["guild_id"]
    live.write_text("{not json")  # relay corrupted mid-write
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        fetch(base + "/api/snapshot")
    assert excinfo.value.code == 503  # no last-good lying
