# Session 2026-07-11 — read-views deepening slice 2 (skills, structures, mini-map, staleness, energy)

> **Status:** `complete`

## Plan

Extend the read-only rendering to the remaining uncovered READ-contract
fields, in one branch/PR — rendering work only, no contract, schema,
write-path, or auth changes:

1. **Skills panel** — per-miner `skills` allocation on the miner card.
2. **Structures view** — per-miner `structures` with counts/tiers.
3. **Position mini-map** — plot each miner's `position` {x, y} on a small
   grid per depth band; degrade gracefully when positions are missing or
   malformed.
4. **Snapshot staleness UX** — surface `generated_at` age prominently
   ("snapshot 3m old") with the contract's staleness guidance (60 s
   cadence, stale beyond 3 missed cycles ≈ 180 s — the prose numbers, the
   schema carries no delivery facts). Age computed client-side, once per
   page load, honest states (unknown timestamp → say so; future timestamp
   → clock-skew warning).
5. **Energy display** — current vs the schema's 0–60 bound plus an
   `updated_at`-aware "as of <UTC instant>" presentation; no live ticking.
6. **Tests** — pytest coverage for every new shaping path, extending
   `tests/test_views.py`; all field lists/shapes stay schema-derived
   (position/energy required-field lists join the existing slot-enum /
   xp-fields wiring), never hand-copied.

Constraints honored: stdlib-only backend, no build step, no new
dependencies; contract + schema files untouched; write/auth paths
untouched; frontend talks to the backend only via `/api/views`;
`control/status.md` / `control/inbox.md` untouched.

## Close-out

- `server/views.py`: new schema wiring (`position_fields()` /
  `energy_fields()` from the schema's `required` lists) + shapers —
  `rank_counts` (countMap → `[name, value]` pairs, highest first, alpha
  tiebreak, open keys never filtered), `shape_position` (schema fields or
  honest None), `shape_energy` (required fields + the 0–60 bound,
  `updated_at` passthrough), `build_minimap` (per-band `points` /
  `unplotted` / integer `bounds`, None bounds when nothing plots),
  `parse_generated_at` (ISO 8601 UTC → epoch, None when unusable) and
  `build_staleness` (epoch + prose cadence/threshold constants
  `SNAPSHOT_CADENCE_SECONDS`/`STALE_AFTER_SECONDS`; age math stays
  client-side). `shape_miner` now ships `skills`, `structures`, shaped
  `position` and the deepened `energy`; `build_views` adds `staleness` +
  `minimap` blocks. No route changes — `/api/views` simply carries more.
- Frontend: staleness line in the header (`fresh`/`warn`/`stale` states,
  age computed against the browser clock at page load, never ticking),
  mini-map section (per-band plots with padded proportional placement,
  "position unknown" listed honestly, empty bands skipped), Skills +
  Structures card sections via `rankedList`, energy meter bar (low-energy
  color, "as of <UTC>" from `updated_at`). `web/index.html` gains the
  `snapshot-staleness` line + `minimap` section; `web/style.css` styles
  them.
- verify: `python3 -m pytest -q` → 187 passed, 1 skipped (163 + 24 new in
  `tests/test_views.py`: schema wiring for position/energy fields,
  rank_counts ordering/tolerance, position/energy shaping, mini-map
  panels/bounds/unplotted/empty, generated_at parsing incl. offset and
  naive forms, staleness block honesty, envelope + garbage-tolerance
  extensions, slice-2 frontend anchor smoke). `python3 bootstrap.py check
  --strict` → all checks passed. Headless render smoke (scratchpad DOM
  stub over the real `app.js` + real `/api/views` payloads): full,
  empty-guild, garbage-staleness, views-down, fresh-90s, stale-2h and
  future-timestamp scenarios all render without throwing, honest text in
  each state.
- Claim `control/claims/claude-slice2-deep-views.md` rides this PR;
  removal is deferred to the next control-lane PR, per the
  write-contract-established pattern.
- Contract fields still unrendered after this slice: the miner-level
  required set is now fully rendered; what remains is only the OPEN
  additive tail — extra keys beyond the required pairs inside `position`
  (future discovery fields) and `energy` (future regen fields), and
  `xp.game`/`xp.shared_total` appear only on the leaderboard, not the
  card face.

## 💡 Session idea

The mini-map plots one band at a time but says nothing about CO-location —
two miners on the same cell overlap invisibly. A server-side
"cell occupancy" grouping (same {x, y} → one point with N names) would be
a five-line change in `build_minimap` and would let the frontend render a
"×2" badge instead of stacked dots.

## ⟲ Previous-session review

The read-views-deepening session's schema-wiring pattern (derive lists
from the schema at import, pin them EQUAL in a wiring test) extended to
position/energy fields with zero friction — the pattern scales. Its
guard recipe about `renderDepthRace` still shaping inline in `app.js`
remains open (not this slice's scope — rendering additions only); recipe
unchanged: consume `views.miners` in `renderDepthRace` and extend
`tests/test_views.py::test_views_route_serves_shaped_document` with the
race ordering assertion. One friction found here: the sample snapshot's
`energy.updated_at` (1783728000 = 2026-07-11T00:00Z) does not match its
`generated_at` (12:00Z) — harmless, but a fixture regeneration should
align them so "as of" strings read plausibly next to the snapshot age.

- **📊 Model:** fable-5 · standard effort · task-class: read-view deepening slice 2 (server shaping + frontend render + tests) (build)
