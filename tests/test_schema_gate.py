"""Schema gate — the committed sample must conform to the v1 READ contract.

Contract prose: docs/mining-data-contract.md.
Machine contract: schemas/mining_snapshot.v1.schema.json (draft 2020-12).
"""

import copy
import json
from datetime import datetime
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

REPO_ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT_PATH = REPO_ROOT / "data" / "sample_snapshot.json"
SCHEMA_PATH = REPO_ROOT / "schemas" / "mining_snapshot.v1.schema.json"


@pytest.fixture(scope="module")
def schema():
    return json.loads(SCHEMA_PATH.read_text())


@pytest.fixture(scope="module")
def snapshot():
    return json.loads(SNAPSHOT_PATH.read_text())


@pytest.fixture(scope="module")
def validator(schema):
    return Draft202012Validator(schema, format_checker=FormatChecker())


def test_schema_itself_is_valid_draft_2020_12(schema):
    Draft202012Validator.check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"


def test_sample_snapshot_conforms_to_v1(validator, snapshot):
    errors = sorted(validator.iter_errors(snapshot), key=lambda e: list(e.path))
    details = "\n".join(
        f"- at {'/'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in errors
    )
    assert not errors, f"sample violates the v1 contract:\n{details}"


def test_generated_at_is_parseable_utc_iso8601(snapshot):
    # jsonschema's date-time format check is best-effort (skipped without
    # optional validators installed) — parse it for real so the gate is real.
    parsed = datetime.fromisoformat(snapshot["generated_at"].replace("Z", "+00:00"))
    assert parsed.tzinfo is not None, "generated_at must carry an explicit UTC offset"


def test_schema_version_is_the_v1_const(schema, snapshot):
    assert schema["properties"]["schema_version"]["const"] == "1"
    assert snapshot["schema_version"] == "1"


def test_snowflakes_are_strings_not_numbers(snapshot):
    # Discord snowflakes exceed IEEE-754 double precision; a JSON number
    # would be silently corrupted by JS consumers.
    assert isinstance(snapshot["guild_id"], str)
    for miner in snapshot["miners"]:
        assert isinstance(miner["suid"], str)
        assert isinstance(miner["guild_id"], str)


# --- negative cases: the gate must actually bite -------------------------


def _first_error(validator, payload):
    return next(iter(validator.iter_errors(payload)), None)


def test_gate_rejects_missing_envelope_field(validator, snapshot):
    broken = copy.deepcopy(snapshot)
    del broken["generated_at"]
    assert _first_error(validator, broken) is not None


def test_gate_rejects_wrong_schema_version(validator, snapshot):
    broken = copy.deepcopy(snapshot)
    broken["schema_version"] = "2"
    assert _first_error(validator, broken) is not None


def test_gate_rejects_undeclared_envelope_field(validator, snapshot):
    broken = copy.deepcopy(snapshot)
    broken["surprise"] = True
    assert _first_error(validator, broken) is not None


def test_gate_rejects_missing_required_miner_field(validator, snapshot):
    broken = copy.deepcopy(snapshot)
    del broken["miners"][0]["mining_inventory"]
    assert _first_error(validator, broken) is not None


def test_gate_rejects_numeric_snowflake(validator, snapshot):
    broken = copy.deepcopy(snapshot)
    broken["guild_id"] = 987654321098765432
    assert _first_error(validator, broken) is not None


def test_gate_rejects_unknown_equipment_slot(validator, snapshot):
    broken = copy.deepcopy(snapshot)
    broken["miners"][0]["equipment"]["hat"] = "party hat"
    assert _first_error(validator, broken) is not None


def test_gate_rejects_out_of_band_values(validator, snapshot):
    for field, value in (
        ("depth", 4),  # oracle bands are 0-3
        ("vault_level", 7),  # oracle range is 0-6
    ):
        broken = copy.deepcopy(snapshot)
        broken["miners"][0][field] = value
        assert _first_error(validator, broken) is not None, field
    broken = copy.deepcopy(snapshot)
    broken["miners"][0]["energy"]["current"] = 61  # oracle cap is 60
    assert _first_error(validator, broken) is not None


def test_gate_allows_dynamic_map_keys(validator, snapshot):
    # Item/skill/structure names are oracle-owned and open-ended: new names
    # must NOT trip the gate.
    grown = copy.deepcopy(snapshot)
    miner = grown["miners"][0]
    miner["mining_inventory"]["unobtainium"] = 1
    miner["vault"]["unobtainium"] = 2
    miner["skills"]["spelunking"] = 1
    miner["structures"]["observatory"] = 1
    miner["gear_wear"]["unobtainium pick"] = 0
    assert _first_error(validator, grown) is None
