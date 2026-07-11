"""Write-contract schema gate — proposals and responses must conform to v1.

Contract prose: docs/mining-write-contract.md (TEST GUILD ONLY).
Machine contracts: schemas/mining_action.v1.schema.json (proposal) and
schemas/mining_action_response.v1.schema.json (executor answer), both
draft 2020-12 — same gate style as tests/test_schema_gate.py for the
READ contract.
"""

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

REPO_ROOT = Path(__file__).resolve().parent.parent
ACTION_SCHEMA_PATH = REPO_ROOT / "schemas" / "mining_action.v1.schema.json"
RESPONSE_SCHEMA_PATH = REPO_ROOT / "schemas" / "mining_action_response.v1.schema.json"

TEST_GUILD_ID = "987654321098765432"  # the committed sample snapshot's guild
KNOWN_SUID = "100000000000000001"  # DeepDelver in data/sample_snapshot.json
ACTION_UUID = "0f4b3a2c-9d1e-4c5b-8a7f-6e5d4c3b2a19"  # valid lowercase UUIDv4

# One VALID proposal fixture per enum action — the gate proves every action
# the contract names is actually expressible.
VALID_ACTIONS = {
    "mine": {},
    "descend": {},
    "ascend": {},
    "sell": {"item": "iron", "quantity": 5},
    "vault_deposit": {"amount": 100},
    "vault_withdraw": {"amount": 40},
    "equip": {"item": "diamond pickaxe", "slot": "tool"},
}


def make_proposal(action, params):
    return {
        "contract_version": "1",
        "action_id": ACTION_UUID,
        "guild_id": TEST_GUILD_ID,
        "suid": KNOWN_SUID,
        "action": action,
        "params": params,
    }


ACCEPTED_RESPONSE = {
    "contract_version": "1",
    "action_id": ACTION_UUID,
    "status": "accepted",
    "reason_code": "ok",
    "message": "mined 3 stone",
    "replayed": False,
    "result": {
        "state_delta": {"mining_inventory": {"stone": 45}, "energy": {"current": 40, "updated_at": 1783728060}},
        "snapshot_generated_at": "2026-07-11T12:01:00Z",
    },
}

REJECTED_RESPONSE = {
    "contract_version": "1",
    "action_id": ACTION_UUID,
    "status": "rejected",
    "reason_code": "guild_not_allowed",
    "message": "guild is not on the test-guild allowlist",
    "replayed": False,
}


@pytest.fixture(scope="module")
def action_schema():
    return json.loads(ACTION_SCHEMA_PATH.read_text())


@pytest.fixture(scope="module")
def response_schema():
    return json.loads(RESPONSE_SCHEMA_PATH.read_text())


@pytest.fixture(scope="module")
def action_validator(action_schema):
    return Draft202012Validator(action_schema, format_checker=FormatChecker())


@pytest.fixture(scope="module")
def response_validator(response_schema):
    return Draft202012Validator(response_schema, format_checker=FormatChecker())


def _first_error(validator, payload):
    return next(iter(validator.iter_errors(payload)), None)


def _assert_valid(validator, payload):
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
    details = "\n".join(
        f"- at {'/'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in errors
    )
    assert not errors, f"payload violates the v1 write contract:\n{details}"


# --- the schemas themselves ------------------------------------------------


def test_schemas_are_valid_draft_2020_12(action_schema, response_schema):
    for schema in (action_schema, response_schema):
        Draft202012Validator.check_schema(schema)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"


def test_contract_version_is_the_v1_const(action_schema, response_schema):
    assert action_schema["properties"]["contract_version"]["const"] == "1"
    assert response_schema["properties"]["contract_version"]["const"] == "1"


def test_action_enum_matches_the_documented_safe_set(action_schema):
    assert action_schema["properties"]["action"]["enum"] == list(VALID_ACTIONS)


def test_equip_slot_enum_matches_the_read_contract(action_schema):
    read_schema = json.loads(
        (REPO_ROOT / "schemas" / "mining_snapshot.v1.schema.json").read_text()
    )
    read_slots = read_schema["$defs"]["miner"]["properties"]["equipment"][
        "propertyNames"
    ]["enum"]
    write_slots = action_schema["$defs"]["equipParams"]["properties"]["slot"]["enum"]
    assert write_slots == read_slots


# --- proposals: every enum action has a validating fixture -----------------


@pytest.mark.parametrize("action", sorted(VALID_ACTIONS))
def test_valid_proposal_per_action(action_validator, action):
    _assert_valid(action_validator, make_proposal(action, VALID_ACTIONS[action]))


# --- proposals: the gate must bite ------------------------------------------


def test_proposal_rejects_missing_envelope_field(action_validator):
    for missing in ("contract_version", "action_id", "guild_id", "suid", "action", "params"):
        broken = make_proposal("mine", {})
        del broken[missing]
        assert _first_error(action_validator, broken) is not None, missing


def test_proposal_rejects_undeclared_envelope_field(action_validator):
    broken = make_proposal("mine", {})
    broken["surprise"] = True
    assert _first_error(action_validator, broken) is not None


def test_proposal_rejects_wrong_contract_version(action_validator):
    broken = make_proposal("mine", {})
    broken["contract_version"] = "2"
    assert _first_error(action_validator, broken) is not None


def test_proposal_rejects_non_uuid4_action_id(action_validator):
    for bad in ("", "not-a-uuid", ACTION_UUID.upper(),
                "0f4b3a2c-9d1e-1c5b-8a7f-6e5d4c3b2a19"):  # version nibble != 4
        broken = make_proposal("mine", {})
        broken["action_id"] = bad
        assert _first_error(action_validator, broken) is not None, bad


def test_proposal_rejects_numeric_snowflakes(action_validator):
    # Snowflakes are STRINGS on the wire (IEEE-754 — same rule as the READ contract).
    broken = make_proposal("mine", {})
    broken["guild_id"] = 987654321098765432
    assert _first_error(action_validator, broken) is not None
    broken = make_proposal("mine", {})
    broken["suid"] = 100000000000000001
    assert _first_error(action_validator, broken) is not None


def test_proposal_rejects_action_outside_the_closed_enum(action_validator):
    # sell_all, buy, craft… stay out of v1 until added to the schema itself.
    for bad in ("sell_all", "buy", "craft", "explore", "unequip", ""):
        broken = make_proposal("mine", {})
        broken["action"] = bad
        assert _first_error(action_validator, broken) is not None, bad


def test_proposal_rejects_params_for_parameterless_actions(action_validator):
    for action in ("mine", "descend", "ascend"):
        broken = make_proposal(action, {"turbo": True})
        assert _first_error(action_validator, broken) is not None, action


def test_proposal_rejects_bad_sell_params(action_validator):
    for bad in (
        {},  # missing both
        {"item": "iron"},  # missing quantity
        {"quantity": 5},  # missing item
        {"item": "", "quantity": 5},  # empty item name
        {"item": "iron", "quantity": 0},  # below minimum
        {"item": "iron", "quantity": 2.5},  # not an integer
        {"item": "iron", "quantity": 5, "price": 10},  # undeclared field
    ):
        assert _first_error(action_validator, make_proposal("sell", bad)) is not None, bad


def test_proposal_rejects_bad_vault_params(action_validator):
    for action in ("vault_deposit", "vault_withdraw"):
        for bad in ({}, {"amount": 0}, {"amount": -5}, {"amount": "10"},
                    {"amount": 10, "extra": 1}):
            assert _first_error(
                action_validator, make_proposal(action, bad)
            ) is not None, (action, bad)


def test_proposal_rejects_bad_equip_params(action_validator):
    for bad in (
        {},
        {"item": "diamond pickaxe"},  # missing slot
        {"slot": "tool"},  # missing item
        {"item": "party hat", "slot": "hat"},  # slot outside the closed set
        {"item": "", "slot": "tool"},  # empty item name
    ):
        assert _first_error(action_validator, make_proposal("equip", bad)) is not None, bad


# --- responses ---------------------------------------------------------------


def test_valid_accepted_response(response_validator):
    _assert_valid(response_validator, ACCEPTED_RESPONSE)


def test_valid_rejected_responses_for_every_error_code(
    response_validator, response_schema
):
    codes = [c for c in response_schema["properties"]["reason_code"]["enum"] if c != "ok"]
    for code in codes:
        rejected = copy.deepcopy(REJECTED_RESPONSE)
        rejected["reason_code"] = code
        _assert_valid(response_validator, rejected)


def test_valid_replayed_response(response_validator):
    replay = copy.deepcopy(ACCEPTED_RESPONSE)
    replay["replayed"] = True
    _assert_valid(response_validator, replay)


def test_response_rejects_missing_required_field(response_validator):
    for missing in ("contract_version", "action_id", "status", "reason_code",
                    "message", "replayed"):
        broken = copy.deepcopy(REJECTED_RESPONSE)
        del broken[missing]
        assert _first_error(response_validator, broken) is not None, missing


def test_response_rejects_undeclared_field(response_validator):
    broken = copy.deepcopy(REJECTED_RESPONSE)
    broken["surprise"] = True
    assert _first_error(response_validator, broken) is not None


def test_response_rejects_accepted_without_result(response_validator):
    broken = copy.deepcopy(ACCEPTED_RESPONSE)
    del broken["result"]
    assert _first_error(response_validator, broken) is not None


def test_response_rejects_accepted_with_non_ok_reason(response_validator):
    broken = copy.deepcopy(ACCEPTED_RESPONSE)
    broken["reason_code"] = "economy_rejection"
    assert _first_error(response_validator, broken) is not None


def test_response_rejects_rejected_with_ok_reason(response_validator):
    broken = copy.deepcopy(REJECTED_RESPONSE)
    broken["reason_code"] = "ok"
    assert _first_error(response_validator, broken) is not None


def test_response_rejects_rejected_carrying_a_result(response_validator):
    broken = copy.deepcopy(REJECTED_RESPONSE)
    broken["result"] = copy.deepcopy(ACCEPTED_RESPONSE["result"])
    assert _first_error(response_validator, broken) is not None


def test_response_rejects_reason_code_outside_the_taxonomy(response_validator):
    broken = copy.deepcopy(REJECTED_RESPONSE)
    broken["reason_code"] = "computer_says_no"
    assert _first_error(response_validator, broken) is not None


def test_response_rejects_result_missing_its_required_parts(response_validator):
    for missing in ("state_delta", "snapshot_generated_at"):
        broken = copy.deepcopy(ACCEPTED_RESPONSE)
        del broken["result"][missing]
        assert _first_error(response_validator, broken) is not None, missing
