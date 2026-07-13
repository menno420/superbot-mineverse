# Session — 2026-07-13 — HTTP-status ↔ reason_code coherence on relayed envelopes

> **Status:** `in-progress`
> **Branch:** `claude/status-coherence-check`
> **Venue:** lane worker session (coordinator green-light wave — generative
> rung: decide-and-flag, CI-green).

**Goal:** land the second recorded follow-up from PR #60's decide-and-flag
record (`.sessions/2026-07-13-write-path-hardening.md`: "NOT enforced (and
flagged in the PR): the prose HTTP-status↔reason_code mapping table — a
conformant envelope under a mismatched status still relays"). Today
`_serve_action` (server/app.py) relays any schema-CONFORMANT executor
envelope verbatim even when the HTTP status contradicts the envelope's
content (`ok` under a 4xx/5xx, a rejection reason_code under 200). Plan:

1. Derive the status↔envelope coherence rules from
   docs/mining-write-contract.md's "HTTP status mapping" table — the closed
   reason_code taxonomy maps 1:1 to expected statuses; nothing invented
   beyond the contract's prose.
2. Wire the check into `server/response_validation.py` (coherence layer ON
   TOP of schema conformance, same honest
   `502 {"error": "invalid executor response"}` path in `_serve_action`).
3. Tests: coherent success/rejection/replay pairs still relay verbatim;
   each incoherent class → 502; jsonschema agreement sweep untouched.
4. Contract prose: mention the coherence layer in the
   verbatim-after-conformance-check paragraph (Status badge stays in the
   first 12 lines).

Baseline measured on base main @ 5a14f03 (PR #68's serve helper present):
**522 passed + 1 skipped**.
