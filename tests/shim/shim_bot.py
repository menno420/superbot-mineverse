"""Dev/test-only MOCK of the bot-side WRITE-contract executor — TEST GUILD ONLY.

This shim makes docs/mining-write-contract.md executable before the real
bot-side endpoint exists in the superbot repo. It implements the whole v1
contract against an IN-MEMORY copy of the committed sample snapshot:

- HMAC transport auth (the canonical implementation in
  ``server/actions.py`` — both sides share one signing function).
- Full request-schema validation (``schemas/mining_action.v1.schema.json``)
  with the contract's reason-code classification (``unknown_action`` /
  ``invalid_params`` / ``malformed_request`` / ``unsupported_contract_version``).
- Hard test-guild allowlisting: only the loaded snapshot's guild (or an
  explicit allowlist) is accepted; everything else is ``guild_not_allowed``.
- Deterministic state transitions: mine → +1 depth-band ore, −1 energy,
  +5 xp; descend/ascend → depth ±1 inside the 0..max_depth bands; sell →
  inventory−− coins++ (flat 10 coins/item); vault_deposit/vault_withdraw →
  coins ⇄ vault["coins"]; equip → flips the gear slot.
- An in-memory AUDIT LOG entry per authenticated action — accepted or
  rejected — carrying exactly the contract's required fields (action_id,
  action, suid, guild_id, params_digest, outcome, timestamp,
  contract_version, origin="web"). Pre-auth rejections
  (invalid_signature / stale_timestamp) and schema-invalid bodies are not
  attributable to an actor and are not audited.
- Idempotent replay: same ``action_id`` + same body inside the run →
  the ORIGINAL response with ``replayed: true``, never a re-execution;
  same ``action_id`` + different body → ``replayed_action`` (409).
- OPT-IN deterministic rate limiting (contract § Rate limits): pass
  ``rate_limit=(max_requests, window_seconds)`` — or run standalone with
  ``SHIM_RATE_LIMIT=10/10``, the contract's burst default — to enforce a
  per-``(suid, guild_id)`` sliding-window budget. Over budget → 429
  ``rate_limited`` plus a ``Retry-After`` header (integer seconds), never
  stored for idempotency. DEFAULT OFF: without the knob no request is ever
  rate-limited, byte-identical to the pre-knob shim, so the hermetic suite
  and the conformance sweep's default behavior stay deterministic.

Run it locally for development (never in production — it is a toy economy
over fixture data):

    python3 -m tests.shim.shim_bot          # port 8100, or SHIM_PORT env

then point the web server at it:

    MINING_WRITE_ENDPOINT=http://127.0.0.1:8100/relay/mining/action \\
    MINING_WRITE_SHARED_SECRET=<same secret as the shim> \\
    python3 server/app.py

This module lives under ``tests/`` (not ``server/``) on purpose: the
architecture contract keeps ``server/`` stdlib-only, and the shim leans on
the dev-only ``jsonschema`` gate dependency. Nothing in the production
server path imports it.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import re
import sys
import time
from collections import deque
from datetime import datetime, timezone
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from server import actions  # noqa: E402 — the shared canonical signing

ACTION_PATH = "/relay/mining/action"
ACTION_SCHEMA_PATH = REPO_ROOT / "schemas" / "mining_action.v1.schema.json"
SNAPSHOT_PATH = REPO_ROOT / "data" / "sample_snapshot.json"

SELL_PRICE_PER_ITEM = 10  # flat and deterministic — a toy economy
XP_PER_MINE = 5
ORE_BY_DEPTH = ("stone", "iron", "gold", "diamond")  # depth bands 0-3
# Echoed when a proposal is too broken to carry a usable action_id
# (contract: responses always echo a UUID-shaped action_id).
PLACEHOLDER_ACTION_ID = "00000000-0000-4000-8000-000000000000"

_UUID_V4 = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


class EconomyRejection(Exception):
    """The toy economy said no (mirrors the bot's domain rejections)."""


class _RateLimited(Exception):
    """Over the per-``(suid, guild_id)`` budget — carries the backoff hint."""

    def __init__(self, proposal: dict, retry_after: int) -> None:
        super().__init__(f"retry after {retry_after}s")
        self.proposal = proposal
        self.retry_after = retry_after


class ShimState:
    """The whole executor: state + auth + idempotency + audit, in memory."""

    def __init__(
        self,
        snapshot: dict,
        secret: str,
        *,
        allowed_guilds: set[str] | None = None,
        now=time.time,
        rate_limit: tuple[int, float] | None = None,
    ) -> None:
        self.snapshot = copy.deepcopy(snapshot)
        self.secret = secret
        # TEST GUILD ONLY: default allowlist is exactly the fixture's guild.
        self.allowed_guilds = (
            set(allowed_guilds)
            if allowed_guilds is not None
            else {self.snapshot["guild_id"]}
        )
        self.now = now
        # OPT-IN limiter (contract § Rate limits): (max_requests,
        # window_seconds) per (suid, guild_id); None (the default) = OFF.
        self.rate_limit = rate_limit
        self.audit_log: list[dict] = []
        # (suid, guild_id) -> recent request times inside the window
        self._request_times: dict[tuple[str, str], deque] = {}
        # (guild_id, action_id) -> {digest, http_status, response}
        self._idempotency: dict[tuple[str, str], dict] = {}
        self._validator = Draft202012Validator(
            json.loads(ACTION_SCHEMA_PATH.read_text()),
            format_checker=FormatChecker(),
        )
        self._action_enum = json.loads(ACTION_SCHEMA_PATH.read_text())[
            "properties"
        ]["action"]["enum"]

    # --- entry point ------------------------------------------------------

    def handle(
        self, method: str, path: str, headers, body: bytes
    ) -> tuple[int, dict, dict]:
        """One proposal in, one (http_status, envelope, extra_headers) out.

        ``extra_headers`` is ``{}`` on every path except the opt-in 429,
        which carries the contract's ``Retry-After`` (integer seconds).
        """
        try:
            status, response = self._dispatch(method, path, headers, body)
            return status, response, {}
        except _RateLimited as limit:
            # Contract § Rate limits: 429 rate_limited + Retry-After, and
            # the proposal is NOT stored for idempotency (a retry of the
            # same action_id after the window is a fresh evaluation).
            # Post-auth and attributable, so it IS audited like every
            # other rejection.
            status, response = self._response(
                429, limit.proposal["action_id"], "rate_limited",
                "over the per-actor budget; "
                f"retry after {limit.retry_after}s")
            self._audit(limit.proposal, "rejected:rate_limited")
            return status, response, {"Retry-After": str(limit.retry_after)}

    def _dispatch(
        self, method: str, path: str, headers, body: bytes
    ) -> tuple[int, dict]:
        """Auth → parse → schema-classify → the schema-valid pipeline."""
        auth_failure = actions.verify(
            self.secret,
            method,
            path,
            headers.get(actions.HEADER_TIMESTAMP) or "",
            body,
            headers.get(actions.HEADER_SIGNATURE) or "",
            now=self.now(),
        )
        if auth_failure == "invalid_signature":
            return self._response(401, PLACEHOLDER_ACTION_ID, "invalid_signature",
                                  "request signature is missing or wrong")
        if auth_failure == "stale_timestamp":
            return self._response(401, PLACEHOLDER_ACTION_ID, "stale_timestamp",
                                  "signature timestamp outside the skew window")

        try:
            proposal = json.loads(body)
        except ValueError:
            return self._response(400, PLACEHOLDER_ACTION_ID, "malformed_request",
                                  "body is not valid JSON")
        if not isinstance(proposal, dict):
            return self._response(400, PLACEHOLDER_ACTION_ID, "malformed_request",
                                  "body is not a JSON object")
        action_id = self._echoable_action_id(proposal)
        if proposal.get("contract_version") != actions.CONTRACT_VERSION:
            return self._response(400, action_id, "unsupported_contract_version",
                                  "this executor speaks contract version 1 only")
        if proposal.get("action") not in self._action_enum:
            return self._response(400, action_id, "unknown_action",
                                  "action is outside the closed v1 enum")
        errors = list(self._validator.iter_errors(proposal))
        if errors:
            reason = (
                "invalid_params"
                if any("params" in error.absolute_path for error in errors)
                else "malformed_request"
            )
            return self._response(400, action_id, reason, errors[0].message)

        return self._handle_valid(proposal, body)

    # --- the schema-valid path ---------------------------------------------

    def _handle_valid(self, proposal: dict, body: bytes) -> tuple[int, dict]:
        self._consume_budget(proposal)  # may raise _RateLimited
        key = (proposal["guild_id"], proposal["action_id"])
        digest = hashlib.sha256(body).hexdigest()
        stored = self._idempotency.get(key)
        if stored is not None:
            if stored["digest"] == digest:
                # Idempotent replay: the ORIGINAL response, never re-executed,
                # never re-audited.
                replay = copy.deepcopy(stored["response"])
                replay["replayed"] = True
                return stored["http_status"], replay
            return self._reject_audited(  # key reuse IS a client anomaly;
                proposal, None, 409, "replayed_action",  # never stored
                "action_id was already used with a different body")

        if proposal["guild_id"] not in self.allowed_guilds:
            return self._reject_audited(
                proposal, digest, 403, "guild_not_allowed",
                "guild is not on the test-guild allowlist "
                "(live cutover is the owner's stage-d flag)")
        miner = self._find_miner(proposal["suid"], proposal["guild_id"])
        if miner is None:
            return self._reject_audited(
                proposal, digest, 404, "actor_not_found",
                "no mining state for that player in this guild")

        try:
            delta, message = self._execute(miner, proposal["action"],
                                           proposal["params"])
        except EconomyRejection as veto:
            return self._reject_audited(proposal, digest, 422,
                                        "economy_rejection", str(veto))

        status, response = self._response(
            200, proposal["action_id"], "ok", message, result={
                "state_delta": delta,
                "snapshot_generated_at": self._iso_now(),
            })
        self._remember(proposal, digest, status, response)
        self._audit(proposal, "accepted:ok")
        return status, response

    # --- deterministic toy transitions --------------------------------------

    def _execute(self, miner: dict, action: str, params: dict):
        max_depth = int(self.snapshot.get("max_depth", len(ORE_BY_DEPTH) - 1))
        if action == "mine":
            if miner["energy"]["current"] < 1:
                raise EconomyRejection("not enough energy to mine")
            ore = ORE_BY_DEPTH[miner["depth"]]
            miner["mining_inventory"][ore] = (
                miner["mining_inventory"].get(ore, 0) + 1
            )
            miner["energy"]["current"] -= 1
            miner["energy"]["updated_at"] = int(self.now())
            miner["xp"]["game_total"] += XP_PER_MINE
            miner["xp"]["shared_total"] += XP_PER_MINE
            return (
                {"mining_inventory": miner["mining_inventory"],
                 "energy": miner["energy"], "xp": miner["xp"]},
                f"mined 1 {ore}",
            )
        if action == "descend":
            if miner["depth"] >= max_depth:
                raise EconomyRejection("already at the deepest band")
            miner["depth"] += 1
            delta = {"depth": miner["depth"]}
            if miner["depth"] > miner["record_depth"]:
                miner["record_depth"] = miner["depth"]
                delta["record_depth"] = miner["record_depth"]
            return delta, f"descended to depth {miner['depth']}"
        if action == "ascend":
            if miner["depth"] <= 0:
                raise EconomyRejection("already at the surface")
            miner["depth"] -= 1
            return {"depth": miner["depth"]}, f"ascended to depth {miner['depth']}"
        if action == "sell":
            item, quantity = params["item"], params["quantity"]
            carried = miner["mining_inventory"].get(item, 0)
            if carried < quantity:
                raise EconomyRejection(
                    f"cannot sell {quantity}× {item}: only {carried} carried")
            if carried == quantity:
                del miner["mining_inventory"][item]
            else:
                miner["mining_inventory"][item] = carried - quantity
            proceeds = quantity * SELL_PRICE_PER_ITEM
            miner["coins"] += proceeds
            return (
                {"coins": miner["coins"],
                 "mining_inventory": miner["mining_inventory"]},
                f"sold {quantity}× {item} for {proceeds} coins",
            )
        if action == "vault_deposit":
            amount = params["amount"]
            if miner["coins"] < amount:
                raise EconomyRejection(
                    f"cannot deposit {amount} coins: only {miner['coins']} held")
            miner["coins"] -= amount
            miner["vault"]["coins"] = miner["vault"].get("coins", 0) + amount
            return ({"coins": miner["coins"], "vault": miner["vault"]},
                    f"deposited {amount} coins into the vault")
        if action == "vault_withdraw":
            amount = params["amount"]
            banked = miner["vault"].get("coins", 0)
            if banked < amount:
                raise EconomyRejection(
                    f"cannot withdraw {amount} coins: only {banked} banked")
            if banked == amount:
                del miner["vault"]["coins"]
            else:
                miner["vault"]["coins"] = banked - amount
            miner["coins"] += amount
            return ({"coins": miner["coins"], "vault": miner["vault"]},
                    f"withdrew {amount} coins from the vault")
        if action == "equip":
            miner["equipment"][params["slot"]] = params["item"]
            return ({"equipment": miner["equipment"]},
                    f"equipped {params['item']} in the {params['slot']} slot")
        raise EconomyRejection(f"unhandled action {action}")  # unreachable

    # --- plumbing ------------------------------------------------------------

    def _consume_budget(self, proposal: dict) -> None:
        """Sliding-window rate limiter (contract § Rate limits) — OPT-IN.

        ``rate_limit`` unset (the default) → no budget exists and nothing
        is recorded. Armed, the budget counts every authenticated,
        schema-valid proposal per ``(suid, guild_id)`` — replays included;
        the limiter shields everything behind it. It sits AFTER auth (an
        unattributable request can neither consume nor probe a budget)
        and BEFORE the idempotency store (rate-limited proposals are
        never stored). ``Retry-After`` is the integer seconds until the
        oldest in-window request ages out — deterministic under the
        injectable ``now`` clock.
        """
        if self.rate_limit is None:
            return
        max_requests, window = self.rate_limit
        now = self.now()
        times = self._request_times.setdefault(
            (proposal["suid"], proposal["guild_id"]), deque()
        )
        while times and now - times[0] >= window:
            times.popleft()
        if len(times) >= max_requests:
            raise _RateLimited(
                proposal, max(1, math.ceil(times[0] + window - now))
            )
        times.append(now)

    def _find_miner(self, suid: str, guild_id: str) -> dict | None:
        for miner in self.snapshot.get("miners") or []:
            if miner["suid"] == suid and miner["guild_id"] == guild_id:
                return miner
        return None

    @staticmethod
    def _echoable_action_id(proposal: dict) -> str:
        candidate = proposal.get("action_id")
        if isinstance(candidate, str) and _UUID_V4.match(candidate):
            return candidate
        return PLACEHOLDER_ACTION_ID

    def _iso_now(self) -> str:
        return (
            datetime.fromtimestamp(self.now(), tz=timezone.utc)
            .strftime("%Y-%m-%dT%H:%M:%SZ")
        )

    def _response(self, http_status, action_id, reason_code, message, *,
                  result=None) -> tuple[int, dict]:
        response = {
            "contract_version": actions.CONTRACT_VERSION,
            "action_id": action_id,
            "status": "accepted" if reason_code == "ok" else "rejected",
            "reason_code": reason_code,
            "message": message,
            "replayed": False,
        }
        if result is not None:
            response["result"] = result
        return http_status, response

    def _reject_audited(self, proposal, digest, http_status, reason_code,
                        message):
        """A post-auth rejection: audited, and (contract) stored for replay.

        ``digest=None`` (the ``replayed_action`` key-reuse case) skips the
        store — a 409 must never overwrite the original action's response.
        """
        status, response = self._response(
            http_status, proposal["action_id"], reason_code, message)
        self._remember(proposal, digest, status, response)
        self._audit(proposal, f"rejected:{reason_code}")
        return status, response

    def _remember(self, proposal, digest, http_status, response) -> None:
        if digest is None:
            return
        key = (proposal["guild_id"], proposal["action_id"])
        self._idempotency[key] = {
            "digest": digest,
            "http_status": http_status,
            "response": copy.deepcopy(response),
        }

    def _audit(self, proposal: dict, outcome: str) -> None:
        self.audit_log.append({
            "action_id": proposal["action_id"],
            "action": proposal["action"],
            "suid": proposal["suid"],
            "guild_id": proposal["guild_id"],
            "params_digest": hashlib.sha256(
                json.dumps(proposal["params"], separators=(",", ":"),
                           sort_keys=True).encode("utf-8")
            ).hexdigest(),
            "outcome": outcome,
            "timestamp": self._iso_now(),
            "contract_version": actions.CONTRACT_VERSION,
            "origin": "web",
        })


class ShimHandler(BaseHTTPRequestHandler):
    """Thin HTTP wrapper: one POST route into :meth:`ShimState.handle`."""

    state: ShimState

    def __init__(self, *args, state: ShimState | None = None, **kwargs):
        if state is not None:
            self.state = state
        super().__init__(*args, **kwargs)

    def do_POST(self):  # noqa: N802 (http.server API name)
        route, _, _ = self.path.partition("?")
        if route != ACTION_PATH:
            self._send_json(404, {"error": "unknown route"})
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        body = self.rfile.read(length) if length > 0 else b""
        status, response, extra = self.state.handle(
            "POST", route, self.headers, body
        )
        self._send_json(status, response, extra_headers=extra)

    def do_GET(self):  # noqa: N802 — nothing to read here
        self._send_json(404, {"error": "unknown route"})

    def _send_json(
        self, status: int, payload: dict, *, extra_headers: dict | None = None
    ) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for name, value in (extra_headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        pass  # keep test output clean


def make_shim_server(
    host: str = "127.0.0.1",
    port: int = 0,
    *,
    secret: str,
    snapshot_path: Path = SNAPSHOT_PATH,
    allowed_guilds: set[str] | None = None,
    now=time.time,
    rate_limit: tuple[int, float] | None = None,
) -> tuple[ThreadingHTTPServer, ShimState]:
    """Build (but don't start) the shim — port 0 picks a free port.

    ``rate_limit=(max_requests, window_seconds)`` arms the opt-in
    per-``(suid, guild_id)`` limiter; ``None`` (the default) keeps it OFF.
    """
    state = ShimState(
        json.loads(snapshot_path.read_text()),
        secret,
        allowed_guilds=allowed_guilds,
        now=now,
        rate_limit=rate_limit,
    )
    handler = partial(ShimHandler, state=state)
    return ThreadingHTTPServer((host, port), handler), state


def parse_rate_limit(raw: str | None) -> tuple[int, float] | None:
    """``SHIM_RATE_LIMIT=10/10`` → ``(10, 10.0)`` — max_requests per
    window_seconds (the contract's burst default). Unset/empty → OFF."""
    if not raw:
        return None
    max_str, sep, window_str = raw.partition("/")
    if not sep:
        raise ValueError(
            "SHIM_RATE_LIMIT must look like '10/10'"
            " (max_requests/window_seconds)"
        )
    return int(max_str), float(window_str)


def main() -> None:
    secret = os.environ.get(actions.ENV_SECRET) or "shim-dev-secret-not-a-secret"
    port = int(os.environ.get("SHIM_PORT", "8100"))
    rate_limit = parse_rate_limit(os.environ.get("SHIM_RATE_LIMIT"))
    server, state = make_shim_server(
        port=port, secret=secret, rate_limit=rate_limit
    )
    host, bound_port = server.server_address[:2]
    limit_note = (
        f"{state.rate_limit[0]} requests / {state.rate_limit[1]:g} s"
        " per (suid, guild)"
        if state.rate_limit
        else "off (opt in: SHIM_RATE_LIMIT=10/10)"
    )
    print(
        "mineverse BOT SHIM (TEST ECONOMY — dev/test only, never production)\n"
        f"  endpoint: http://{host}:{bound_port}{ACTION_PATH}\n"
        f"  allowed guilds: {sorted(state.allowed_guilds)}\n"
        f"  rate limit: {limit_note}\n"
        f"  secret: ${actions.ENV_SECRET}"
        f"{' (using the dev default)' if actions.ENV_SECRET not in os.environ else ''}"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
