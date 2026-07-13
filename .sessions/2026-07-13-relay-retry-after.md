# Session — 2026-07-13 — relay contract-relevant executor headers (Retry-After on 429)

> **Status:** `in-progress`
> **Branch:** `claude/relay-retry-after`
> **Venue:** lane worker session (coordinator green-light wave — generative
> rung: decide-and-flag, CI-green, flip-race practice).

**Goal:** land the recorded 💡 from
`.sessions/2026-07-13-status-coherence-check.md` (PR #69): the contract
promises a `Retry-After` header (integer seconds) on every 429
`rate_limited` rejection (docs/mining-write-contract.md § Rate limits and
the HTTP status mapping table), but `server/actions.py::propose` returns
only `(status, body)` — `res.headers` / `err.headers` are dropped — and
`_serve_action` sets only its own Content-Type/Length/Cache-Control, so a
relayed 429 reaches the browser WITHOUT the backoff hint the contract
promises clients.

Plan: allowlist relay (contract-relevant headers only, never a blanket
passthrough — executor headers can carry internals), threaded through
`propose`'s return into `_serve_action`; shim audit for a 429 path;
fake-executor tests pinning verbatim relay on 429, header absence staying
relayable, and non-429 never growing executor headers; one contract
sentence iff the prose is silent on the relay side.

Baseline measured on base main @ 5a12fee (PR #69's squash):
**539 passed + 1 skipped**.

## Close-out

_(pending)_

- **📊 Model:** fable-5 · standard effort · task-class: recorded 💡 follow-up — Retry-After relay allowlist on the write path (build)
