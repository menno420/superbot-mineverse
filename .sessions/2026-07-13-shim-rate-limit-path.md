# Session — 2026-07-13 — reference rate-limit path in the executor shim

> **Status:** `in-progress`
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

Plan: an OPT-IN, deterministic rate-limit mode on the shim — default OFF
so every existing test and the conformance sweep's default behavior stay
byte-identical — answering 429 `{ok-shaped envelope, reason_code:
"rate_limited"}` with a `Retry-After` header, schema-conformant and
status-coherent, driven by the shim's already-injectable `now` clock so
tests stay deterministic. Knob shape and pipeline placement are
decide-and-flag records for the close-out.

Baseline measured on base main @ 234e8f7 (PR #71's squash):
**545 passed + 1 skipped**.
