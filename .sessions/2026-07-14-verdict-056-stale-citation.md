# Session — 2026-07-14 — VERDICT 056 applied: stale threshold gains its measured basis

> **Status:** `in-progress`
> **Branch:** `claude/verdict-056-stale-citation`
> **Venue:** lane worker session (ORDER 006 item 2 — EAP final-night
> worklist; ORDER 007 doctrine in force: correctness outranks speed,
> no gate relaxed).

**Goal:** apply sim-lab VERDICT 056 (finalized APPROVE, sim-lab
`control/outbox.md` L999–L1008 @ `32ff5c3`) to the one place this repo
owns it: the T=180 s snapshot stale indicator already exists end-to-end
(`server/views.py` `SNAPSHOT_CADENCE_SECONDS`/`STALE_AFTER_SECONDS` +
`build_staleness()`, `web/app.js` `renderStaleness()`), so the verdict's
deliverable here is documentation truth, not plumbing: (a) the contract's
"default suggestion: 3 missed cycles ≈ 180 s" hedge in
`docs/mining-data-contract.md` § Delivery expectations becomes the
measured wording the verdict's recommendation (1) spells out, with the
citable basis (`sims/verdict-056-snapshot-stale-threshold/results.json` +
`REPORT.md`) and the verdict's own named boundaries kept honest
(invented-but-pinned disturbance widths, i.i.d.-miss lean, 60 s-cadence
worlds only); (b) a citation comment lands at the
`server/views.py` constants so the code anchor points at the evidence;
(c) NOTHING behavioral — the constant stays 180, zero test deltas
expected (575 passed + 1 skipped stays the bar).
