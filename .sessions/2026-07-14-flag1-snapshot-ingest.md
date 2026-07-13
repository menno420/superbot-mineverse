# Session — 2026-07-14 — FLAG-1 snapshot-ingest RECEIVE endpoint

> **Status:** `in-progress`
> **Branch:** `claude/flag1-snapshot-ingest`
> **Venue:** lane worker session (ORDER 006 item 1 — EAP final-night
> worklist; ORDER 007 production-grade doctrine adopted: correctness
> outranks speed, no gate relaxed).

**Goal:** build the FLAG-1 snapshot-ingest RECEIVE endpoint that
ORDER 006 item 1 names: superbot PR #2058 POSTs a v1 snapshot to
`MINING_SNAPSHOT_RELAY_URL` every ~60 s, but `server/app.py` `do_POST`
handles only `/api/action` — the receiving endpoint exists nowhere.
Ship: HMAC-verified `POST /api/snapshot/ingest` (reusing the repo's ONE
canonical signing scheme, `server/actions.py` `sign`/`verify` —
`X-Mineverse-Signature`/`X-Mineverse-Timestamp`, HMAC-SHA256 over
`METHOD\nPATH\nTIMESTAMP\nsha256(body)`, ±300 s skew, constant-time) →
v1-validate with the existing runtime validator
(`server/snapshot_validation.py`) BEFORE anything persists → atomic
whole-document replace into the `MINING_SNAPSHOT_PATH` file the read
seam already re-reads fresh per request. Secret from
`MINING_SNAPSHOT_RELAY_SHARED_SECRET` (host env, never the repo);
secret or path unset → fail closed (honest 503, unsigned data never
accepted). Full test coverage in the repo's existing HTTP-seam style;
stdlib-only prod path; docs ledger kept truthful. The item-3
spec addendum to `docs/mining-data-contract.md` is the NEXT slice —
this card records the facts it needs.

## Close-out

_(to be written at flip time)_

## 💡 Session idea

_(placeholder — a real deduped idea lands at flip time)_

## ⟲ Previous-session review

_(placeholder — written at flip time from the newest prior card)_

- **📊 Model:** fable-5 · standard effort · task-class: FLAG-1 snapshot-ingest RECEIVE endpoint — HMAC-verified POST → v1-validate → atomic persist (build)
