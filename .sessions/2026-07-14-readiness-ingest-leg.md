# Session — 2026-07-14 — readiness check: ingest-route leg

> **Status:** `complete`
> **Branch:** `claude/readiness-ingest-leg`
> **Venue:** lane worker session (ORDER 006 item 5 — EAP final-night
> worklist; ORDER 007 production-grade doctrine adopted: correctness
> outranks speed, no gate relaxed).

**Goal:** now that the FLAG-1 receive endpoint is on main (PR #88,
`POST /api/snapshot/ingest`), extend `scripts/readiness_check.py` with
the ingest-route leg ORDER 006 item 5 names, in the script's own shape
(opt-in probe flag, injected prober, SET/UNSET-only reporting — a value
is NEVER printed): one deliberately UNSIGNED POST to the ingest route
must draw the contract's **401** (configured — `invalid_signature` /
`stale_timestamp` before anything is parsed) or the honest **503**
(unconfigured fail-closed), and **NEVER 200** — an unsigned acceptance
is a security failure the check must red loudly. Endpoint sourced from
`MINING_SNAPSHOT_RELAY_URL` (the exact env var superbot #2058 pushes
to), mirroring how `--probe` sources `MINING_WRITE_ENDPOINT`. Update
`docs/live-prod-cutover.md` §6 for the new leg; tests in
`tests/test_readiness.py` (injected env dicts + loopback-only servers,
including the REAL app server in both configured and unconfigured
modes — no secrets, no non-loopback network, exactly like CI).

## Close-out

Shipped on `claude/readiness-ingest-leg` (base: main @ `a73b4ea` — the
item-4 squash, itself atop the #89/#92 lane-C merges and #88's ingest
endpoint).

`scripts/readiness_check.py` grew the ingest leg in the script's own
grammar rather than a new one: `--probe-ingest` (opt-in flag, mirrored
on `--probe`), endpoint from `MINING_SNAPSHOT_RELAY_URL` (mirroring how
`--probe` sources `MINING_WRITE_ENDPOINT`; the name is superbot #2058's
own, so the leg verifies the exact URL the bot pushes to),
`probe_ingest_endpoint()` beside `probe_endpoint()`, injected
`ingest_prober=` on `build_report` for network-free wiring tests, and
the SET/UNSET-only hygiene held — no detail string ever carries a URL
or value. Decision semantics: 401 with the canonical transport-auth
reason (`invalid_signature`/`stale_timestamp` — `INGEST_401_REASONS`
transcribes `server/actions.verify`'s two returns) → ok/configured; 503
with exactly `snapshot ingest not configured` → ok/fail-closed (honest
degraded mode IS a correct unsigned answer); **HTTP 200 → FAILED in
security terms** ("accepted an UNSIGNED snapshot push"); any other
status/body → FAILED honestly. URL unset → leg skipped, never failed:
the READ relay is optional at every stage per the cutover doc §1, so
skipping keeps exit-code semantics for the six required vars untouched.

Tests (12 new in `tests/test_readiness.py`, style-matched to the file's
existing three sections): the REAL app server on loopback in BOTH honest
modes (configured 401 — asserting nothing persisted; unconfigured 503)
via the shared `serve` fixture, stub servers for the three answers the
real server must never give (unsigned 200, non-canonical 401, stray
418), unreachable honesty, and the injected-prober report wiring
(skip=ready, failure reds even with all six SET, success reads READY,
prober untouched without the flag, sentinel URL never printed).
End-to-end CLI smoke run pre-commit: real configured server → `ingest
probe: ok — … rejected the unsigned probe (invalid_signature)`, exit 0,
nothing persisted. `docs/live-prod-cutover.md` §6: usage line, a
`--probe-ingest` bullet (naming the 200-is-a-security-failure rule and
the § "Ingest transport & authentication" contract anchor), and the
test-coverage bullet updated. Ledger line added.

Verified pre-flip in this container: `python3 -m pytest -q` →
**587 passed, 1 skipped** (575 baseline + 12 new);
`python3 bootstrap.py check --strict` exit 0 (tail pasted in the PR).

## 💡 Session idea

`scripts/conformance_run.py` already vendors the readiness probe once
(`_load_readiness_probe()`, scripts/conformance_run.py:186-194, reusing
`readiness_check.probe_endpoint` via importlib because scripts/ is not a
package) — but its PASS/FAIL verdict covers the WRITE seam only. Now
that the ingest leg exists, the one-command conformance sweep could
grow an opt-in ingest leg the same way: reuse
`readiness_check.probe_ingest_endpoint` through the same importlib
loader (rename the loader to return the module, not one function),
probe `MINING_SNAPSHOT_RELAY_URL` when set, and fold the result into
the existing exit-code taxonomy (0/1/2/3 — probe failures are exit 2)
so a cutover rehearsal exercises BOTH directions of the relay from one
command. Guard recipe: `tests/test_conformance_run.py` is the pattern;
keep the leg skip-not-fail on unset URL exactly like this session's
report wiring. Dedupe checked: no session card, `docs/ideas/` entry, or
finding proposes extending conformance_run beyond the write seam; the
2026-07-13 conformance-runner ledger line scoped itself to
`tests/test_actions.py` explicitly.

## ⟲ Previous-session review

The `2026-07-14-snapshot-contract-constant` card (this seat's own
previous session) holds up on its two riskiest calls: the
deliberately-NOT-wired server import is argued from the repo's two
launch modes with the exact try/except anchors, which is the difference
between "skipped work" and "a decision" — and the audit doc's
"not measured" entries (per-skill-xp reachability, pin freshness) kept
the findings honest where inventing a row would have been easy. Two
things it should have done better, one of which bit THIS session: (1)
its close-out claims base `82b7caa` but the PR actually merged after a
telemetry conflict against lane C's #89/#92 — the merge-resolution
round (keep both lanes' rows) happened after the card flipped, so the
card under-reports the session's real shape; parallel-lane nights make
the born-red→flip window a place where the card's story goes stale
minutes after it's written. (2) Its 💡 gates the slot-map promotion on
the seam ruling but names no owner/venue for noticing when that ruling
lands — a gated idea with no watcher is how backlog items rot; this
card's own idea names its consumer file and test pattern instead.

- **📊 Model:** fable-5 · medium · feature build — readiness-check ingest-route leg — unsigned probe must draw 401/503, never 200
