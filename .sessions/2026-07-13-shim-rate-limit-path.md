# Session — 2026-07-13 — reference rate-limit path in the executor shim

> **Status:** `complete`
> **Branch:** `claude/shim-rate-limit-path`
> **Venue:** lane worker session (coordinator green-light wave — generative
> rung: decide-and-flag, CI-green, flip-race practice).

**Goal:** land the queued flag from
`.sessions/2026-07-13-relay-retry-after.md` (PR #70's card): the reference
executor shim (`tests/shim/shim_bot.py`) has NO rate-limit path at all —
no 429, no `rate_limited`, no `Retry-After` anywhere — yet the contract's
HTTP-status mapping includes the 429 `rate_limited` row and § Rate limits
promises a `Retry-After` header (integer seconds), so the reference
implementation cannot demonstrate that leg of the contract and the
conformance sweep can never exercise it against anything executable.

Baseline measured on base main @ 234e8f7 (PR #71's squash):
**545 passed + 1 skipped**.

## Close-out

Shipped on `claude/shim-rate-limit-path` (base: main @ 234e8f7). No scope
cut. The contract was NOT silent — § Rate limits fully specifies the
behavior (per `(suid, guild_id)`, executor-configurable budgets, 429
`rate_limited` + integer-seconds `Retry-After`, never stored for
idempotency) — the shim had simply never implemented it.

**Knob decision (decided and flagged):** OPT-IN via
`rate_limit=(max_requests, window_seconds)` on `ShimState` /
`make_shim_server`, plus `SHIM_RATE_LIMIT=10/10` (max/window — the
contract's burst default shape) for the standalone `python3 -m
tests.shim.shim_bot` run; `None`/unset — the default — keeps the limiter
OFF and the shim byte-identical to before, so every existing test and the
conformance sweep's default behavior are unchanged (pinned:
`test_rate_limiter_is_opt_in_and_default_off` sends 12 back-to-back
proposals through a knobless shim, zero 429s). The limiter is a sliding
window over the shim's ALREADY-INJECTABLE `now` clock — deterministic by
construction, no sleeps anywhere — and
`Retry-After = max(1, ceil(oldest_in_window + window − now))`, the
seconds until the oldest counted request ages out.

**Placement decision (decided and flagged):** the budget check sits
post-auth (an unattributable request can neither consume nor probe a
budget — signature-first doctrine holds: over-budget + bad signature is
still 401, pinned), post-schema (it needs an attributable
`(suid, guild_id)`), and BEFORE the idempotency store — rate-limited
proposals never reach `_remember` (contract: NOT stored; a byte-identical
retry after the window is a FRESH evaluation, `replayed: false`, pinned).
The budget counts every authenticated schema-valid proposal, replays
included — the contract is silent on whether an idempotent replay consumes
budget; decided that a request is a request (the limiter shields
everything behind it, idempotency store included) and flagged it below. A
429 IS audited (`rejected:rate_limited`) — post-auth and attributable, and
the contract's audit requirement covers every rejection.

**Wiring:** `ShimState.handle` now returns
`(status, envelope, extra_headers)` — `extra_headers` is `{}` everywhere
except the 429, which carries `{"Retry-After": "<seconds>"}`; the
rate-limit path is a `_RateLimited` exception raised in `_handle_valid`
and caught in `handle` (the old `handle` body is `_dispatch`, unchanged).
Callers updated: `ShimHandler.do_POST` (sends the extra headers) and the
one direct caller outside the shim,
`tests/test_response_validation.py::test_shim_responses_conform_at_runtime`
(3-tuple unpack).

**Conformance-mode decision (decided and flagged):** NO real-endpoint
429 test was added. Provoking a REAL executor's rate limit would burn a
whole budget of real actions against executor-configured (not
contract-fixed) limits, and would starve the rest of the sweep's shared
`(suid, guild_id)` budget — turning one probe into cascade failures. The
new tests therefore ALWAYS run in-process on loopback, conformance mode
included (same posture as `fake_executor` — they exercise the reference
shim, not the external target), and the real-endpoint rate-limit check
stays a manual cutover-checklist step. The stale test_actions.py comment
("the shim has NO rate-limit path at all") was updated to point at the
new section.

Coverage (+6 tests, suite **551 passed + 1 skipped**), all in
`tests/test_actions.py`: default-off pin; 429 envelope
schema-conformant + `Retry-After: 10` on the frozen clock + audited;
Retry-After counts down (4 s in → `6`) and the budget recovers after the
window; rate-limited proposals are not stored for idempotency (fresh
evaluation after the window); budget is per-actor and post-auth; and the
end-to-end pin — the REFERENCE shim's own 429 (not the canned executor's)
passes the web relay's conformance + coherence checks and reaches the
browser with `Retry-After` via PR #70's allowlist path. Contract prose:
one clarifying clause in § Enforcement's shim parenthetical naming the
opt-in mode; Status badge untouched. ruff clean; `bootstrap.py check
--strict` green at this flip (mid-slice red only on this card's own
in-progress badge — born-red as intended; the `owner-action-fields`
advisory on control/status.md predates this slice and is advisory-only).

ORDER-038 note: no cross-agent reviewer reply was received or acted on in
this slice; if one lands on the PR, verify its cited line ranges against
EOF at the reviewed head before acting.

## 💡 Session idea

The cutover checklist has no rate-limit leg: docs/live-prod-cutover.md §1
verifies the real executor via the conformance sweep, but the sweep
deliberately never provokes a 429 (tonight's decision — budget-burning,
executor-configured limits), so the one § Rate limits behavior now has an
executable REFERENCE form yet still no verification path against the REAL
endpoint. Guard recipe: add a manual burst-probe step to the §1 checklist
— a DEDICATED probe actor (never the sweep's shared suid, so nothing else
starves), `N = burst+1` rapid `mine` proposals, expect the last to be 429
+ integer `Retry-After` + (idempotency pin) a byte-identical retry after
the window executing fresh — plus one contract sentence settling the
question tonight's shim had to decide alone: whether idempotent REPLAYS
consume rate-limit budget (the shim says yes — a request is a request;
the real bot implementer will hit the same fork and should not have to
guess). Small, checklist-shaped, and it closes the last unexercised row
for real.

## ⟲ Previous-session review

`.sessions/2026-07-13-run-server-lifecycle.md` reviewed at this session's
base (234e8f7, its own squash). Close-out claims reproduced byte-real on
every spot-check: `run_server` is exactly as described
(tests/_server_helpers.py:30-55 — daemon thread over `serve_forever`,
teardown `shutdown()` → `server_close()` → `join(timeout=5)` inside
`finally`); the five collapsed sites are real consumers (conftest.py:54
`base_url`, test_actions.py:138 `shim`, test_readiness.py:112/147/168 —
shim plus both probe stubs); the three factory loops it left alone sit at
EXACTLY its cited lines (_server_helpers.py:79, test_actions.py:706,
test_server_robustness.py:43) and run_server's docstring names all three
with the FIFO/LIFO reason, as claimed; and its "545 passed + 1 skipped —
baseline-identical" matched tonight's independently measured baseline
verbatim. Its 💡 (settle the teardown-order question, then finish the
factory dedupe via ExitStack-or-`started_servers()`) is accurately cited
and still live — tonight's slice ADDED two more `run_server` consumers
(the rate-limit fixtures) but no multi-server factory call, so its
"re-audit call sites first" precondition still resolves the same way.
One nit, same flavor it dinged its own predecessor for: the Goal section's
pre-change cites test_readiness.py:151/178 for the probe stubs, which sit
at :147/:168 after the collapse — drift across its own change, harmless
since the close-out re-located everything. Escalation carry, un-softened:
the bare-📊-line sweep is now NINE reviews old; the next records session
treats "drop it in one line" as the default.

- **📊 Model:** fable-5 · standard effort · task-class: queued 💡 follow-up — reference rate-limit path in the executor shim, 429 + Retry-After (build)
