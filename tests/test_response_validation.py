"""Unit tests for server/response_validation.py — the runtime check of the
executor's WRITE-contract response envelope — plus the conditional-keyword
extensions (``allOf``/``if``/``then``/``else``/``not``) this check required in
the shared schema-derived interpreter (server/snapshot_validation.py).

The authority question is settled by the AGREEMENT SWEEP at the bottom: every
envelope case here is judged by BOTH the stdlib runtime interpreter and the
real jsonschema Draft 2020-12 validator (dev/test dependency), and their
verdicts must match — so the runtime check can never quietly diverge from the
CI schema gate on these shapes.
"""

import json
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from server import response_validation, snapshot_validation  # noqa: E402

RESPONSE_SCHEMA = json.loads(
    (REPO_ROOT / "schemas" / "mining_action_response.v1.schema.json").read_text()
)
JSONSCHEMA_VALIDATOR = Draft202012Validator(
    RESPONSE_SCHEMA, format_checker=FormatChecker()
)

ACTION_ID = "0f0e0d0c-0b0a-4998-8776-655443322110"


def accepted(**overrides) -> dict:
    envelope = {
        "contract_version": "1",
        "action_id": ACTION_ID,
        "status": "accepted",
        "reason_code": "ok",
        "message": "mined 1 diamond",
        "replayed": False,
        "result": {
            "state_delta": {"depth": 2, "coins": 18470},
            "snapshot_generated_at": "2026-07-13T02:00:00Z",
        },
    }
    envelope.update(overrides)
    return envelope


def rejected(**overrides) -> dict:
    envelope = {
        "contract_version": "1",
        "action_id": ACTION_ID,
        "status": "rejected",
        "reason_code": "economy_rejection",
        "message": "not enough energy to mine",
        "replayed": False,
    }
    envelope.update(overrides)
    return envelope


def without(envelope: dict, key: str) -> dict:
    trimmed = dict(envelope)
    del trimmed[key]
    return trimmed


# One list, two validators (see module docstring). Label → (envelope, valid?).
ENVELOPE_CASES = {
    "accepted with result": (accepted(), True),
    "rejected without result": (rejected(), True),
    "rejected replayed": (rejected(replayed=True), True),
    "every rejection reason": (rejected(reason_code="rate_limited"), True),
    "not an object": ([], False),
    "empty object": ({}, False),
    "accepted MISSING result (if/then)": (without(accepted(), "result"), False),
    "rejected WITH result (if/then/not)": (
        rejected(result=accepted()["result"]),
        False,
    ),
    "rejected with reason ok": (rejected(reason_code="ok"), False),
    "accepted with non-ok reason": (accepted(reason_code="internal_error"), False),
    "reason outside the taxonomy": (rejected(reason_code="mystery"), False),
    "action_id not a uuid v4": (accepted(action_id="not-a-uuid"), False),
    "undeclared extra property": (accepted(surprise=1), False),
    "missing required message": (without(rejected(), "message"), False),
    "replayed not a boolean": (rejected(replayed="yes"), False),
    "result missing state_delta": (
        accepted(result={"snapshot_generated_at": "2026-07-13T02:00:00Z"}),
        False,
    ),
    "wrong contract version": (rejected(contract_version="2"), False),
}


@pytest.mark.parametrize("label", ENVELOPE_CASES)
def test_envelope_error_verdicts(label):
    envelope, valid = ENVELOPE_CASES[label]
    problem = response_validation.envelope_error(json.dumps(envelope).encode())
    if valid:
        assert problem is None, f"{label}: unexpectedly refused: {problem}"
    else:
        assert problem is not None, f"{label}: unexpectedly accepted"


@pytest.mark.parametrize("label", ENVELOPE_CASES)
def test_runtime_interpreter_agrees_with_jsonschema(label):
    """The stdlib interpreter and the real Draft 2020-12 validator must agree."""
    envelope, valid = ENVELOPE_CASES[label]
    jsonschema_says = not list(JSONSCHEMA_VALIDATOR.iter_errors(envelope))
    assert jsonschema_says == valid, f"{label}: case list is wrong about jsonschema"
    runtime_says = (
        response_validation.envelope_error(json.dumps(envelope).encode()) is None
    )
    assert runtime_says == jsonschema_says, f"{label}: runtime/jsonschema drift"


def test_non_json_body_is_refused_with_a_plain_message():
    assert response_validation.envelope_error(b"<html>oops</html>") == (
        "executor body is not valid JSON"
    )
    assert response_validation.envelope_error(b"") == (
        "executor body is not valid JSON"
    )


# --- HTTP-status ↔ reason_code coherence (a layer ON TOP of conformance) ----
# PR #60's flagged follow-up: the contract's "HTTP status mapping" table pairs
# every reason_code with exactly one status; envelope_error(http_status=...)
# enforces it. NOT part of the jsonschema agreement sweep above — jsonschema
# judges the body alone and knows nothing of HTTP statuses.


def coherent_envelope(reason_code: str) -> dict:
    return accepted() if reason_code == "ok" else rejected(reason_code=reason_code)


def test_status_table_matches_the_schema_taxonomy():
    """EXPECTED_HTTP_STATUS transcribes the contract's mapping table; its keys
    must be exactly the schema's closed reason_code enum, so an additive
    taxonomy change can never silently skip the coherence check."""
    assert set(response_validation.EXPECTED_HTTP_STATUS) == set(
        RESPONSE_SCHEMA["properties"]["reason_code"]["enum"]
    )


def test_every_reason_code_coheres_only_with_its_table_status():
    """Exhaustive sweep: each of the 13 reason_codes passes under exactly its
    contract status and is refused under every other status in the table."""
    statuses = sorted(set(response_validation.EXPECTED_HTTP_STATUS.values()))
    for reason, expected in response_validation.EXPECTED_HTTP_STATUS.items():
        body = json.dumps(coherent_envelope(reason)).encode()
        for status in statuses:
            problem = response_validation.envelope_error(body, http_status=status)
            if status == expected:
                assert problem is None, f"{reason} under {status}: {problem}"
            else:
                assert problem is not None and "incoherent" in problem, (
                    f"{reason} under {status} was not refused"
                )


def test_replay_repeats_the_original_status_rule():
    """'An idempotent replay repeats the original response's HTTP status' —
    so `replayed: true` obeys the same table row as the original, for stored
    accepts AND stored rejections."""
    for status, envelope in (
        (200, accepted(replayed=True)),
        (422, rejected(replayed=True)),
    ):
        body = json.dumps(envelope).encode()
        assert (
            response_validation.envelope_error(body, http_status=status) is None
        )


def test_omitting_http_status_keeps_the_schema_only_verdict():
    """The coherence layer is opt-in per call: without http_status the
    verdict is conformance-only (the incoherent pair below passes)."""
    body = json.dumps(rejected()).encode()  # economy_rejection ⇔ 422
    assert response_validation.envelope_error(body) is None
    assert response_validation.envelope_error(body, http_status=200) is not None


def test_conformance_verdict_wins_over_coherence():
    """A body that fails the schema reports the schema violation (and draws
    the 502) whatever the status — coherence never runs on a non-envelope."""
    problem = response_validation.envelope_error(
        json.dumps(rejected(reason_code="ok")).encode(), http_status=200
    )
    assert problem is not None and "incoherent" not in problem


def test_table_drift_from_the_schema_fails_loud():
    """If the taxonomy ever grows a code the table lacks (caught in CI by the
    equality pin above, but belt-and-braces at runtime), the verdict is a
    refusal — never a silently skipped check. Exercised through the schema
    injection seam since the committed schema cannot reach this branch."""
    problem = response_validation.envelope_error(
        json.dumps({"reason_code": "mystery"}).encode(),
        http_status=200,
        schema={"type": "object"},
    )
    assert problem is not None and "no contract HTTP status mapping" in problem


def test_shim_responses_conform_at_runtime():
    """The dev shim's envelopes — the contract's executable reference — must
    pass the runtime check too (the app now refuses non-conformant answers),
    INCLUDING status↔reason_code coherence with the status the shim chose."""
    from tests.shim.shim_bot import make_shim_server

    server, state = make_shim_server(port=0, secret="s3")
    server.server_close()  # never started — ShimState.handle is called directly
    for name, body in {
        "pre-auth reject": b"{}",
        "malformed": b"{not json",
    }.items():
        status, envelope, _headers = state.handle(
            "POST", "/relay/mining/action", {}, body
        )
        assert (
            response_validation.envelope_error(
                json.dumps(envelope).encode(), http_status=status
            )
            is None
        ), name


# --- the interpreter extensions themselves (allOf / if / then / else / not) --


def test_allof_checks_every_subschema():
    schema = {"allOf": [{"type": "object"}, {"required": ["a"]}]}
    assert snapshot_validation.validate_value({"a": 1}, schema) == {"a": 1}
    with pytest.raises(snapshot_validation.SnapshotInvalid, match="allOf"):
        snapshot_validation.validate_value({}, schema)


def test_if_then_else_branches():
    schema = {
        "if": {"properties": {"kind": {"const": "big"}}, "required": ["kind"]},
        "then": {"required": ["size"]},
        "else": {"required": ["name"]},
    }
    snapshot_validation.validate_value({"kind": "big", "size": 1}, schema)
    snapshot_validation.validate_value({"kind": "small", "name": "x"}, schema)
    with pytest.raises(snapshot_validation.SnapshotInvalid, match="then"):
        snapshot_validation.validate_value({"kind": "big"}, schema)
    with pytest.raises(snapshot_validation.SnapshotInvalid, match="else"):
        snapshot_validation.validate_value({"kind": "small"}, schema)


def test_not_refuses_a_match():
    schema = {"not": {"required": ["forbidden"]}}
    snapshot_validation.validate_value({"fine": 1}, schema)
    with pytest.raises(snapshot_validation.SnapshotInvalid, match="must not"):
        snapshot_validation.validate_value({"forbidden": 1}, schema)


def test_drift_guard_still_fails_loud_inside_conditionals():
    """An unimplemented keyword inside an ``if``/``not`` subschema must raise
    (fail loud), never be swallowed as an ordinary "does not match"."""
    for schema in (
        {"if": {"anyOf": [{"type": "object"}]}, "then": {"type": "object"}},
        {"not": {"anyOf": [{"type": "string"}]}},
    ):
        with pytest.raises(
            snapshot_validation.SnapshotInvalid, match="unimplemented"
        ):
            snapshot_validation.validate_value({}, schema)


def test_response_schema_is_fully_interpretable():
    """Every keyword the committed response schema uses is implemented — the
    drift guard never fires on a conformant envelope (belt for the sweep)."""
    snapshot_validation.validate_value(accepted(), RESPONSE_SCHEMA)


# --- committed-schema cache: parsed once, explicit clear seam ----------------


def test_load_schema_is_cached_with_an_explicit_clear_seam(tmp_path):
    # Same shape as snapshot_validation's cache pin: the COMMITTED response
    # schema is parsed once (lru_cache); the executor's response BODY is of
    # course still judged fresh per call — only the ruler is cached.
    original_path = response_validation.SCHEMA_PATH
    response_validation.load_schema.cache_clear()
    try:
        first = response_validation.load_schema()
        assert response_validation.load_schema() is first  # cached, not re-parsed
        edited = tmp_path / "edited.schema.json"
        edited.write_text('{"type": "object"}')
        response_validation.SCHEMA_PATH = edited
        # An edit is invisible until the explicit seam is used …
        assert response_validation.load_schema() is first
        # … and cache_clear() genuinely picks the new file up.
        response_validation.load_schema.cache_clear()
        assert response_validation.load_schema() == {"type": "object"}
    finally:
        response_validation.SCHEMA_PATH = original_path
        response_validation.load_schema.cache_clear()
