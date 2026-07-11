# Session 2026-07-11 — micro-polish: suid + guild id + xp.game on the read views

> **Status:** `complete`

## Plan

Small read-only rendering polish — frontend painting + tests only, no
contract, schema, server, write-path, or auth changes:

1. **suid identity line** — `suid` already ships in the shaped miner
   (`/api/views`) and keys the my-miner lookup, but never paints. Add a
   subtle identity line to the miner card (which the my-miner view
   reuses), muted and small.
2. **guild id in the header** — `guild_id` already passes through the
   views envelope but never paints. Show it once, on the existing
   `snapshot-meta` line next to version + generated-at, near the
   staleness line.
3. **xp.game on the card face** — the card's XP line hardcodes the word
   "mining"; replace it with the contract's `xp.game` field (honest `?`
   when absent) so the card paints the field instead of assuming it.
4. **Defensive coverage** — the contract keeps position/energy/xp
   PERMISSIVE beyond their required fields; position extras were already
   pinned tolerated, add the energy + xp twins, plus passthrough pins for
   the newly painted fields and a frontend anchor smoke.

Constraints honored: stdlib-only backend, vanilla HTML/JS/CSS, no build
step, no new dependencies; schema stays the single source of truth (no
server shaping changes were even needed — all three fields already ride
`/api/views`); `control/status.md` / `control/inbox.md` untouched.

## Close-out

- `web/app.js`: `renderMinerCard` gains an `identity-line` paragraph
  (`suid <value>`, "unknown" when absent) right under the name; the XP
  line now reads `Level N · M <xp.game> XP · coins` with `?` for a
  missing game name; `render()` appends `· guild <guild_id>` to the
  `snapshot-meta` header line ("unknown" when absent). No new HTML
  anchors needed — `web/index.html` untouched.
- `web/style.css`: one rule — `.identity-line` (muted, 0.75rem).
- `tests/test_views.py`: 4 new tests (187 → 191 passed) —
  `test_shape_energy_ignores_extra_open_fields` and
  `test_shaped_miner_xp_ignores_extra_open_fields` (additive extras
  inside energy/xp never leak into or break the shaped projection,
  completing the position twin that already existed),
  `test_shaped_miner_carries_suid_and_xp_game` (passthrough pins for the
  newly painted fields over the sample snapshot), and
  `test_frontend_paints_identity_and_xp_game` (served-frontend anchor
  smoke: `identity-line` in app.js + style.css, `miner.suid`,
  `views.guild_id`, `xp.game`).
- verify: `python3 -m pytest -q` → 191 passed, 1 skipped (was 187 + 1);
  `python3 bootstrap.py check --strict` → all checks passed. (Local env
  note: `jsonschema` had to be pip-installed for the schema-gate test
  modules to collect — test-only dependency, CI installs it already.)
- Claim `control/claims/claude-micro-polish-identity-xp.md` rides this
  PR; removal is deferred to the next control-lane PR, per the
  established pattern.
- Card-face coverage after this slice: every miner-level required field
  now paints somewhere, and `xp.game`/`suid`/`guild_id` paint on the
  card face / header; `xp.shared_total` still appears only on the XP
  leaderboard, not the card face (deliberate — it is cross-game data).

## 💡 Session idea

The header now shows the raw guild snowflake, which is honest but
unfriendly. The snapshot has no guild display name — a tiny additive
OPTIONAL `guild_name` envelope field in a future contract rev would let
the header read "guild Rockhounds (98765…)" with zero extra requests.

## ⟲ Previous-session review

The deep-views-slice2 session's close-out map of "still unrendered"
fields made this slice trivial to scope — its OPEN-tail list (extras
inside position/energy, `xp.game` off the card face) was exactly this
PR's checklist, plus the suid/guild_id identity gap. Its friction note
about the sample fixture's `energy.updated_at` (00:00Z) not matching
`generated_at` (12:00Z) remains open and still holds — guard recipe
unchanged: regenerate `data/sample_snapshot.json` aligning
`energy.updated_at` with `generated_at`, then re-pin
`test_shape_energy_carries_schema_fields_and_bound`. The `renderDepthRace`
inline-shaping recipe from the slice-1 session also remains open
(rendering-only slices keep deferring it): consume `views.miners` in
`renderDepthRace` and extend
`tests/test_views.py::test_views_route_serves_shaped_document` with the
race ordering assertion.

- **📊 Model:** (identifier withheld this session) · standard effort · task-class: identity/xp card-face micro-polish (build)
