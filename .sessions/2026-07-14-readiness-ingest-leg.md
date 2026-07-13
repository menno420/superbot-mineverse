# Session — 2026-07-14 — readiness check: ingest-route leg

> **Status:** `in-progress`
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

(pending — flipped with the final commit)
