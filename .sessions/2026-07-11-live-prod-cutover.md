# Session 2026-07-11 — stage (d) PREP: live-prod cutover checklist + readiness check (owner-gated)

> **Status:** `complete`

## Plan

Execute stage (d) PREPARATION (coordinator-assigned, from the staged
queue "[d] LIVE-PROD PREP — owner-flag-gated cutover checklist; never
crossed early"): documentation + readiness tooling ONLY, with the hard
line restated up front — nothing in this session enables, defaults, or
shortcuts any live-prod write path; the owner throws the flag, sessions
only prepare it. Ship (1) `docs/live-prod-cutover.md`: prerequisites with
per-item evidence (real bot-side endpoint passing the shim's contract
fixtures via the `tests/test_actions.py` fixture-seam swap; the OPEN
owner ask making `pytest` a required check; the six host env vars —
`DISCORD_OAUTH_CLIENT_ID`, `DISCORD_OAUTH_CLIENT_SECRET`,
`OAUTH_REDIRECT_URI`, `WEB_SESSION_SIGNING_KEY`, `MINING_WRITE_ENDPOINT`,
`MINING_WRITE_SHARED_SECRET`; Discord redirect registration; end-to-end
audit-trail verification in the test guild), a rate-limits review
(contract's 10/10 s + 60/min per `(suid, guild_id)`, executor-side
enforcement, the UI's no-retry 429 handling), an abuse review
(cookie-theft + `WEB_SESSION_SIGNING_KEY` rotation, CSRF posture as the
code actually is, idempotency/replay, action spam, the
suid-spoofing-impossible argument verified in `server/app.py`, shared-
secret compromise + two-host rotation order), rollback levers
(env-unset degrade paths confirmed in code, allowlist shrink,
audit-driven review, owner vs agent lanes), THE FLAG as its own
unmistakable section (owner adds prod guild ids to the bot-side
allowlist AND says so via a control/inbox.md ORDER; no agent may
decide-and-flag; staged rollout: one guild → observation window →
fleet); (2) `scripts/readiness_check.py` (stdlib-only): the six env vars
reported SET/UNSET — never a value — plus an opt-in `--probe` that sends
one UNSIGNED request and expects the contract's 401 `invalid_signature`
(signature-first means a probe can never execute anything); exit 0 iff
ready; (3) `tests/test_readiness.py`: injected-env tests green with ZERO
env vars, probe tests loopback-only against the existing shim + stubs.

Constraints honored: no server/ or web/ behavior change of any kind; no
secret values anywhere; `control/status.md` / `control/inbox.md`
untouched; claim `control/claims/claude-live-prod-cutover.md` rides this
PR (single-PR arc — close-out removal follows the write-contract
pattern: released by the next PR that touches control/).

## Close-out

- `docs/live-prod-cutover.md` grounds every claim in real repo surfaces:
  env var names from `server/auth.py` + `server/actions.py`
  (`ENV_ENDPOINT`/`ENV_SECRET`), rate limits and reason codes
  (`replayed_action` 409, `rate_limited` 429 + `Retry-After`,
  `guild_not_allowed` 403) from docs/mining-write-contract.md, HMAC
  signing details (`X-Mineverse-Timestamp`/`X-Mineverse-Signature`,
  ±300 s skew, signature-before-timestamp) from `server/actions.py`,
  the exactly-three-keys browser body rule from `server/app.py`
  `_read_action_request`, degrade behavior from `WriteConfig.configured`
  + the UI's disabled-buttons tooltip.
- THE FLAG section is verbatim-unmistakable: live prod turns on ONLY
  when the OWNER (menno420) both (a) adds the prod guild id(s) to the
  bot-side allowlist AND (b) says so via a control/inbox.md ORDER or
  equivalent explicit statement; a fully green checklist is a READY
  flag, never a THROWN one.
- `scripts/readiness_check.py`: presence-only env report (the
  never-print-values rule is itself pinned by
  `test_no_env_value_is_ever_printed` with SENTINEL values), injected
  `environ`/`stdout` for testability, probe validates the response
  envelope structurally (stdlib-only — the full jsonschema gate stays in
  tests/), honest "what it CANNOT check from this repo" list in §6.
- verify: `python3 -m pytest -q` → 130 passed (116 + 14 new in
  `tests/test_readiness.py`; no env vars, no network beyond loopback).
  `python3 bootstrap.py check --strict` → all checks passed.
- Runtime diff surface: zero — no file under `server/`, `web/`,
  `schemas/`, or `data/` changed (docs, scripts, tests, session card,
  claim, ledger lines only).
- Guard recipe (deferred): the conformance-pass session against the
  real bot-side endpoint should add an opt-in fixture switch (e.g.
  `SHIM_CONFORMANCE_BASE_URL` env read inside the `shim` fixture in
  `tests/test_actions.py`) instead of hand-editing the fixture — anchor:
  `shim()` fixture → `make_shim_server` → base URL; the degraded-mode
  block below it must keep using the in-memory `state` and skip under
  the switch.

## 💡 Session idea

`scripts/readiness_check.py --probe` and the shim already agree on the
unsigned-probe handshake; a tiny `--probe-signed` mode gated on
`MINING_WRITE_SHARED_SECRET` could send one syntactically-valid but
economically-impossible action (e.g. `sell` quantity 999999 with a fresh
`action_id`) and expect 422 `economy_rejection` — proving key agreement
end to end without ever mutating state. Worth weighing against the
"never send secrets from tooling" instinct before building.

## ⟲ Previous-session review

Part 2's decision to keep one canonical signing implementation in
`server/actions.py` (shared by web and shim) made this session's abuse
review cheap: every transport claim in the cutover doc cites one file
instead of reconciling two. Friction worth naming: the shim-conformance
"swap the fixture base URL" done-criterion from the part-2 guard recipe
is still a hand-edit — this session documented it verbatim in the
checklist but the missing env-var seam (see guard recipe above) is now
load-bearing for stage d and should land before the real endpoint does.

- **📊 Model:** Claude Fable 5 · standard effort · task-class: cutover checklist + readiness tooling (docs+tooling, owner-gated)
