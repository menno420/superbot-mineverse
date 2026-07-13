# Session — 2026-07-14 — VERDICT 056 applied: stale threshold gains its measured basis

> **Status:** `complete`
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

## Close-out

Shipped on `claude/verdict-056-stale-citation` (base: main @ `82b7caa`,
after the #88 ingest-endpoint squash). Two files, zero behavior:

- `docs/mining-data-contract.md` § Delivery expectations, Staleness
  bullet: the "default suggestion: 3 missed cycles ≈ 180 s" hedge is
  gone; the threshold now reads with the verdict's measured wording
  (false-stale ≤ 1/200 of healthy loads — measured ≈ 1/2070 — mean
  outage detection ≤ 240 s — measured ≈ 145 s — at the pinned model),
  cites VERDICT 056 (sim-lab `control/outbox.md` L999–L1008 @ `32ff5c3`)
  and the exact tables (`sims/verdict-056-snapshot-stale-threshold/
  results.json` + `REPORT.md`), and carries the verdict's own named
  boundaries verbatim-honest: invented-but-pinned disturbance widths
  (jitter ±5/+15 s, miss 1/25, offset ±30 s) with the one-day
  push-timestamp log as the pre-priced calibration step, the i.i.d.-miss
  lean with the burst leg's FS(180) ≈ 0.0161 counter-price, and the
  60 s-cadence-worlds-only scope.
- `server/views.py` constants comment (`SNAPSHOT_CADENCE_SECONDS` /
  `STALE_AFTER_SECONDS`): same citation at the code anchor, pointing
  back at the contract bullet for the boundary detail. The constant
  stays `3 * 60 = 180`; no test, schema, or payload changed.

Verified pre-flip in this container: `python3 -m pytest -q` →
**575 passed, 1 skipped** (identical to the item-1 baseline — docs-only
diff, zero test deltas as predicted) and `python3 bootstrap.py check
--strict` green except the designed born-red hold on this very card
(flipped by this commit).

## 💡 Session idea

The measured 180 now lives in THREE hand-synced copies: `server/views.py
STALE_AFTER_SECONDS` (= 3×60), the `web/app.js` fallback literals
`stale_after_seconds ?? 180` / `cadence_seconds ?? 60` (app.js:740-741,
910), and the contract bullet's prose number — and the only test touching
the JS copy (`tests/test_web_fun.py:118`) pins the literal STRING
`"staleness?.stale_after_seconds ?? 180"`, so views.py and app.js can
drift apart without any gate firing (the JS fallback only matters when
`/api/views` omits staleness, which is exactly when nobody notices).
VERDICT 056 makes this worse to get wrong: a re-drawn band re-reads the
committed exact tables and flips ONE constant — today that flip must find
three. Guard recipe: a cross-surface parity test in `tests/test_web_fun.py`
that regex-extracts the two JS fallback literals from `web/app.js` and
asserts them equal to `views.STALE_AFTER_SECONDS` / `views.
SNAPSHOT_CADENCE_SECONDS`, so any single-copy edit goes PR-red naming the
other copies. Dedup checked: the idea-engine shared-constant idea
(`snapshot-contract-shared-constant-2026-07-11.md`) covers the
schema-required-fields seam only, not delivery constants; no session card
or docs/ideas entry covers cross-surface staleness-constant parity.

## ⟲ Previous-session review

The `2026-07-14-flag1-snapshot-ingest` card is the best kind of handoff:
its "Ingest-auth decision (evidence trail, for the item-3 addendum)"
section pre-paid EXACTLY the research the next two slices consume — env
names with their composition evidence, the no-transport-auth finding in
#2058, the fail-closed rationale — and this session used it verbatim
instead of re-deriving from the diff. The 💡 is a model guard recipe
(named helper signature, both call sites, the exact test files that must
stay green, and a dedup check against two prior cards). Honest nit: the
close-out asserts "existing importers are untouched" for the
`MINING_SNAPSHOT_PATH` move-and-alias but names no test that pins the
alias — if `app.py` ever drops the re-export, the claim's evidence is a
grep, not a red test; one line naming which existing test imports the
alias would have made the claim checkable the way the rest of the card is.

- **📊 Model:** fable-5 · standard effort · task-class: VERDICT 056 application — stale-threshold measured basis into contract doc + views constants citation (docs-only)
