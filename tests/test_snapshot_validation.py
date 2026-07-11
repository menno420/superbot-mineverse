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
