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
from server.app import SNAPSHOT_PATH, WEB_ROOT, make_server  # noqa: E402

SAMPLE = json.loads(SNAPSHOT_PATH.read_text())


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
