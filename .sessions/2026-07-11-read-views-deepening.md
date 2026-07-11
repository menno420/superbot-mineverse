# Session 2026-07-11 — read-views deepening (vault, inventory, ladder, boards, gear)

> **Status:** `in-progress`

## Plan

Deepen the read-only game views over the existing committed snapshot —
rendering work only, on the READ contract v1 as it stands (no contract,
schema, write-path, or auth changes):

1. **Vault panel** — per-miner vault contents + `vault_level` (0–6, tier
   pips) on the miner card and the my-miner view.
2. **Inventory browser** — `mining_inventory` items with counts across the
   guild, ore tiers stone→diamond first, then the rest.
3. **Depth/biome ladder** — visual ladder over depth bands 0–3 and their
   biomes, showing each miner's current `depth` and `record_depth`.
4. **Leaderboards** — extend the depth board with XP-level and coins
   boards (tabbed, small).
5. **Gear panel** — all equipment slots (schema-derived closed enum) with
   per-slot `gear_wear` state, empty slots rendered honestly.
6. **Tests** — every new render path is data-shaped server-side in a pure
   stdlib module (`server/views.py`, exposed read-only as
   `GET /api/views`) so pytest covers it directly; the schema stays the
   single source of truth (slot enum, xp fields, vault/depth/energy
   bounds are DERIVED from `schemas/mining_snapshot.v1.schema.json`,
   never hand-copied).

Constraints honored: backend stays stdlib-only, no build step, no new
dependencies; `docs/mining-data-contract.md` + `schemas/*.json`
unchanged; server write/auth code untouched (one new GET route only);
`control/status.md` / `control/inbox.md` untouched. Degraded mode and
empty stores must render as honest empty states, never crashes.
Close-out: release claim `control/claims/claude-read-views-deepening.md`
in this PR's final commit.

## Close-out

- `server/views.py` (stdlib-only, pure functions over the snapshot dict):
  schema-derived constants (`equipment_slots()` from the slot
  `propertyNames.enum`, `xp_fields()` from the xp `required` list,
  vault/depth/energy bounds from the schema's `maximum`s) plus shapers —
  `group_items` (ore tiers stone→diamond first per the contract prose,
  then the rest alphabetically), `shape_gear` (all slots, wear joined
  from `gear_wear`), `shape_vault`, `build_ladder` (bands 0–max with
  biome names, `here` + `record_only` markers), `build_leaderboards`
  (depth / xp_level / coins), `build_inventory_matrix` (item × miner
  counts with totals), all tolerant of missing/empty fields.
- `GET /api/views` on `server/app.py` (read path only — `do_GET` gained
  one route; write/auth code untouched): serves `build_views(snapshot)`,
  same honest `503 {"error": "snapshot unavailable"}` as `/api/snapshot`
  when the fixture is missing or corrupt.
- Frontend renders everything from `/api/views`: depth/biome ladder
  section, tabbed leaderboards (depth · XP level · coins), guild
  inventory browser (item × miner matrix, ores first), deepened miner
  cards (gear panel over all 9 slots with wear + honest `— empty` slots,
  pack grouped ores/supplies, vault panel with tier pips 0–6); my-miner
  view reuses the shaped card by suid lookup. Empty snapshot → honest
  "no miners" banner; `/api/views` down → error banner, no crash.
- verify: `python3 -m pytest -q` → 154 passed (116 baseline + 38 new in
  `tests/test_views.py`, incl. `/api/views` HTTP round-trips + degraded
  503s + served-frontend wiring smoke). `python3 bootstrap.py check
  --strict` → all checks passed.
- Schema-drift guards baked into the tests: slot list, xp fields and
  bounds are asserted EQUAL to what the schema declares (wiring test),
  so a schema edit that changes the enum breaks `tests/test_views.py`
  before any hand-list could drift.

## 💡 Session idea

The inventory matrix begs for a "total guild wealth" derived stat —
coins + vault + pack valued by a bot-side price table. The price table
is oracle-owned, so the honest path is an OPTIONAL additive `prices`
envelope field in a future v1 schema update; the views layer here could
then rank miners by net worth with zero new wiring.

## ⟲ Previous-session review

The write-ui-shim session's choice to keep `server/actions.py` pure and
stdlib made the pattern for this session obvious: `server/views.py`
mirrors it (pure functions, injected dicts, pytest-first). Friction
worth naming: the frontend's render logic was previously untestable
(all shaping inline in `app.js`); moving shaping server-side fixed it
for these views, but the older sections (`depth race`) still carry
inline JS shaping that pytest cannot see — worth migrating onto
`/api/views` when next touched. Guard recipe: swap
`renderDepthRace(miners, …)` internals in `web/app.js` to consume
`views.miners` (already fetched in `boot()`), then extend
`tests/test_views.py::test_views_route_serves_shaped_document` with the
race's ordering assertion.

- **📊 Model:** Claude Fable 5 · standard effort · task-class: read-view deepening (server shaping + frontend render + tests) (build)
