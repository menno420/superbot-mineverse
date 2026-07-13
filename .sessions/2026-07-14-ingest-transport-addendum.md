# Session — 2026-07-14 — ingest-transport spec addendum to the READ contract

> **Status:** `in-progress`
> **Branch:** `claude/ingest-transport-addendum`
> **Venue:** lane worker session (ORDER 006 item 3 — EAP final-night
> worklist; ORDER 007 doctrine in force: correctness outranks speed,
> no gate relaxed).

**Goal:** record the FLAG-1 transport/auth seam in
`docs/mining-data-contract.md` so both repos share ONE written seam
(ORDER 006 item 3: "record #2058's env-var names, cadence, ingest-auth
decision"). The code shipped in #88 (`POST /api/snapshot/ingest`,
`server/app.py` + `server/ingest.py`, HMAC per the canonical
`server/actions.py` scheme) and the sender half lives in superbot
PR #2058 — but the contract doc still describes only the envelope and
delivery cadence, with the transport facts scattered across the #88
docstrings and the flag1-snapshot-ingest session card's evidence trail.
Ship: a transport & authentication section in the contract doc — sender
env names (`MINING_SNAPSHOT_RELAY_URL` / `MINING_SNAPSHOT_RELAY_GUILD_ID`)
and push behavior, receiver endpoint + HMAC scheme
(`X-Mineverse-Signature`/`X-Mineverse-Timestamp`, string-to-sign,
constant-time, signature before ±300 s skew), the
`MINING_SNAPSHOT_RELAY_SHARED_SECRET` / `MINING_SNAPSHOT_PATH` env pair
with the fail-closed 503 rule, the full response status contract, and
the last-write-wins/no-sequence-key ordering semantics — every fact
verified against the code at HEAD before it is written down. Docs-only;
zero behavior; 575 passed + 1 skipped stays the bar.
