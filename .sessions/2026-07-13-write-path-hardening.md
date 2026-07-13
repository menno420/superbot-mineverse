# Session — 2026-07-13 — write-path hardening (FLAG 2 mineverse side)

> **Status:** `complete`
> **Branch:** `claude/write-path-hardening`
> **Venue:** lane worker session (ORDER 004 night run — item 5, mineverse
> side of the bot-lane FLAG 2 write path).

**Goal:** harden the `POST /api/action` write path around the executor
boundary. Recon (18f1fb3) established that request signing
(HMAC-SHA256, `server/actions.py`), the ±300 s skew window, degraded
modes, and the contract's executor-side `action_id` idempotency all
exist and are tested — none of that is rebuilt. The genuine gaps this
session closes: (1) runtime validation of the executor's response
envelope (today `_serve_action` relays verbatim, unchecked); (2) tests
for the three untested error paths (timeout, garbage body, bad
snapshot on the action route); (3) a recorded replay-protection
posture in `docs/mining-write-contract.md`.

## Close-out

Shipped on `claude/write-path-hardening` (base: main @ b2b41c3, on top
of the merged #57 seam).

**Envelope validation, chosen semantics:** every executor answer —
whatever its HTTP status, 200 included — is validated at runtime
against `schemas/mining_action_response.v1.schema.json` before relay. A
non-conformant or non-JSON body is NEVER relayed: the web server
answers `502 {"error": "invalid executor response"}` — distinct from
the existing `"action relay failed"` 502 (unreachable/timeout), so logs
and frontend can tell "executor gone" from "executor lying". Conformant
envelopes, contract rejections included, relay verbatim exactly as
before. Rationale: a lying 200 is worse than a clean failure; a
conformant 4xx/5xx is first-class contract traffic. NOT enforced (and
flagged in the PR): the prose HTTP-status↔reason_code mapping table —
a conformant envelope under a mismatched status still relays.

**Not a second validator:** `server/response_validation.py` is ~30
lines of loader + `envelope_error(bytes) -> str | None`; the checking
is the SAME schema-derived interpreter that guards snapshot ingestion
(`server/snapshot_validation.py`), extended with the applicators the
response schema uses — `allOf`, `if`/`then`/`else`, `not` — under the
same fail-loud drift guard. Subtlety worth recording: the `if`/`not`
boolean probe (`_passes`) re-raises `_UnhandledKeyword` (new
`SnapshotInvalid` subclass) instead of reading it as "no match", so an
unimplemented keyword inside a conditional subschema still fails loud
(pinned by test). Schema re-read per call, matching the snapshot
pattern — stateless beats a cache on a rate-limited path.

**Timeout seam:** `WriteConfig` gained argument-only
`timeout: float = HTTP_TIMEOUT_SECONDS` (default 10 s untouched;
`propose` now reads `config.timeout`). Deliberately NOT an env var —
the host config surface stays exactly the documented endpoint/secret
pair; tests inject 0.2 s so the timeout→502 test costs ~1 s, not 10.

Coverage (+51 tests, suite **502 passed + 1 skip** from 451 + 1):
`tests/test_actions.py` — executor timeout → 502 (slow canned executor
+ injected cap, elapsed-time pin), six garbage/non-conformant executor
answers (non-JSON 200/500, empty, non-envelope JSON, schema's if/then
violated at runtime: accepted-without-result, non-envelope 409) → the
new 502, the conformant-409-relays-verbatim complement, and
missing/corrupt/schema-invalid snapshot on the action route → 503
pre-relay with the shim's audit log proving the executor was never
contacted. `tests/test_response_validation.py` — envelope verdict
units, a per-case AGREEMENT SWEEP pinning the runtime interpreter's
verdict to the real jsonschema Draft 2020-12 validator on every case,
applicator units, drift-guard-inside-conditionals, and a
shim-envelopes-pass-the-runtime-check pin.

Docs: contract prose now says verbatim-after-conformance-check (§ Web
session → suid binding), plus the new "Replay protection — where it
lives (recorded posture)" subsection: signed ±300 s timestamp on the
wire; `action_id` idempotency executor-side; mineverse stateless by
design, browser mints `action_id`. Status badge untouched in the first
12 lines. No part of replay protection was found to genuinely belong
mineverse-side (a web-side nonce store would duplicate the
executor-side store and break statelessness) — no SIM-REQUEST needed.

## 💡 Session idea

`response_validation.envelope_error` re-reads and re-parses the ~3 KB
response schema on every write relay, and `_snapshot_is_valid` does the
same with the snapshot schema on every request — fine at today's
volumes, but the pattern is now duplicated and both are COMMITTED files
that cannot change under a running server (unlike the live-fed
snapshot, which must be re-read). Guard recipe: a tiny
`functools.lru_cache(maxsize=None)` on the two `load_schema()`
functions only (never on the validated payloads), with a test pinning
that a schema edit + cache_clear is picked up and that live-fed
SNAPSHOT bytes are still re-read fresh per request (the existing
valid→valid→corrupt rewrite test must stay green).

## ⟲ Previous-session review

The `2026-07-13-snapshot-ingestion-seam` card holds up as a model
consume-side seam close-out: the declined-alternative record (NO
last-good cache, with the staleness-vs-outage tradeoff argued from the
statelessness contract) did real work this session — the same doctrine
decided both this session's per-call schema re-read and the
replay-posture "mineverse holds no replay state" bullet. Its flagged
`readiness_check.py` non-change (exit-0 contract vs optional var) is
the right decide-and-flag shape. Its 💡 idea — collapse the four
duplicated load-validate-or-503 blocks onto one
`_load_valid_snapshot()` helper — is still unlanded and got MORE
valuable tonight: `_serve_action` now stacks a third concern
(envelope validation) after those same two, so the helper would shrink
the hardest handler in the file; good micro-slice for a quiet slot.
Carried nit, now five reviews running: the bare-`📊 Model:` line
housekeeping sweep on the older 2026-07-12 cards has neither landed nor
been explicitly dropped — the next records pass really should pick one.

- **📊 Model:** fable-5 · standard effort · task-class: FLAG-2 write-path response hardening — runtime envelope validation + error-path coverage (build)
