# Session — 2026-07-12 — JS logic test harness (backlog item 2)

> **Status:** `complete`
> **Branch:** `claude/js-logic-test-harness`
> **Venue:** lane worker session (coordinator-delegated groomed-backlog slice).

**Goal:** close the JS-logic-test gap
(`docs/ideas/founding-day-groomed-backlog-2026-07-11.md` item 2): no
JavaScript executes in CI today — pytest pins served bytes only, and
`konamiNextProgress` (the PR #40 longest-prefix fix) was verified once via
Playwright, never per-CI-run. Build a minimal harness that runs INSIDE
pytest: shell out to preinstalled `node`, load the REAL `web/app.js` under
minimal browser-global shims, and call named pure functions with JSON test
vectors — `konamiNextProgress` thoroughly, plus the other cleanly-pure
text/shaping helpers worth pinning. Zero new CI infrastructure; tests SKIP
with a clear reason when `node` is absent (matching the repo's existing
conditional-skip pattern). No JSON API behavior change; no npm/package.json.

## Close-out

- **Shipped (PR #48):** `tests/test_js_logic.py` — 19 tests. An embedded
  node runner loads the actual `web/app.js` into a `vm` context whose
  globals carry the minimal shims the file's top level touches (`document`,
  `window.matchMedia`, a forever-pending `fetch` so `boot()` suspends
  without rendering or networking); top-level `function` declarations
  become context properties, so the SAME BYTES the browser runs are called
  with JSON vectors. Reusable seams: `js_call(fn, *args)`,
  `js_fold(fn, init, stream, *extra)` (state-threading trace), and batched
  `run_js_ops` (many ops, one node process).
- **Coverage:** `konamiNextProgress` — the PR #40 longest-prefix hold
  (↑↑ then a third ↑ keeps progress 2), full-sequence trace to 10,
  restart-at-1 vs reset-to-0, case-sensitivity seam, and 14 key streams
  checked step-by-step against a brute-force longest-prefix reference; the
  shipped `KONAMI_SEQUENCE` literal is regex-extracted from source so
  vectors always use the real sequence. Plus `biomeName`/`biomeLabel`,
  `formatAge`, `formatEpochUTC`, `shareCardFileName`, `shareCardGearLines`,
  `shareCardLines`, `packTotal`, `skillRankTotal`.
- **Verify:** `python3 -m pytest -q` → **378 passed, 1 skipped** (baseline
  359+1 plus these 19); `python3 bootstrap.py check --strict` exit 0. Skip
  path proven: with node off PATH the module reports 19 skipped with the
  stated reason. `web/` untouched — served bytes byte-identical.
- Work claim `control/claims/2026-07-12-js-logic-test-harness.md` deleted
  in this close-out commit per convention (the PR is the durable record).

## 💡 Session idea

The vm harness only reaches top-level `function` declarations — global
`const` tables (`KONAMI_SEQUENCE`, `BOARD_TABS`, `ORE_TIER_COLORS`,
`VS_STATS` labels) are lexical bindings invisible as sandbox properties,
which is why this session regex-extracts the Konami literal. But a SECOND
`vm.runInContext("NAME", sandbox)` call in the same context CAN resolve
those lexical bindings: add a `{"type": "get", "name": ...}` op to
`_RUNNER_JS` (tests/test_js_logic.py) and the data tables become pinnable
directly — no regex twin to drift — with `test_js_logic.py::run_js_ops`
as the test target.

## ⟲ Previous-session review

The `2026-07-12-order-003-closeout` card is exactly what a closeout should
be: merges verified at the API with timestamps and payload commits, and its
guard recipe named real code anchors (`parse_model_line`, bootstrap.py
KL-3, the `·`-separated payload) — which let THIS session write a
reconcilable `📊 Model:` line on the first try instead of re-deriving the
grammar. Gap it leaves: the housekeeping baton it flagged (normalizing the
two payload-less 2026-07-12 cards — discord-ua-fix, railway-deployability —
so the reconcile sweep can record them) is still unclaimed.

- **📊 Model:** fable-5 · standard effort · task-class: JS logic test harness — execute web/ pure functions in pytest (test coverage)
