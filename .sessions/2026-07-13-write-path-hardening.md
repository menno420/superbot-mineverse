# Session — 2026-07-13 — write-path hardening (FLAG 2 mineverse side)

> **Status:** `in-progress`
> **Branch:** `claude/write-path-hardening`
> **Venue:** lane worker session (ORDER 004 night run — item 5, mineverse
> side of the bot-lane FLAG 2 write path).

**Goal:** harden the `POST /api/action` write path around the executor
boundary. Recon (18f1fb3) established that request signing
(HMAC-SHA256, `server/actions.py`), the ±300 s skew window, degraded
modes, and the contract's executor-side `action_id` idempotency all
exist and are tested — none of that is rebuilt. The genuine gaps this
session closes: (1) runtime validation of the executor's response
envelope against `schemas/mining_action_response.v1.schema.json`
(today `_serve_action` relays the executor's answer verbatim with no
runtime check — a lying 200 reaches the browser), reusing/extending the
schema-derived interpreter in `server/snapshot_validation.py`; (2) tests
for three untested error paths — executor timeout → 502 (with an
injectable timeout so the suite stays fast), executor garbage/non-JSON
body → the new sanity semantics, and missing/corrupt/schema-invalid
snapshot on the action route → 503 pre-relay; (3) a short
replay-protection posture subsection in `docs/mining-write-contract.md`
recording where replay protection lives (signed timestamp on the wire;
idempotency executor-side; mineverse stateless by design).

## 💡 Session idea

(placeholder — filled at close-out)

- **📊 Model:** fable-5 · standard effort · task-class: FLAG-2 write-path response hardening — runtime envelope validation + error-path coverage (build)
