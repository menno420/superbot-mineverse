# Session 2026-07-14 — eighth achievement: Homesteader

> **Status:** `complete`

## Plan

Improvement-wave lane H, PR 1 of 3 (owner directive 2026-07-14; claim
PR #95). Add ONE new deterministic badge to `ACHIEVEMENT_CATALOG`
(server/views.py): **Homesteader** — owns at least one `home`
structure. Follow the 4-stop recipe documented by the
2026-07-11-sample-data-achievement-earners card (constant, catalog
tuple, `earned_achievements` branch, sample earner) — the committed
sample already gives Homesteader two clean earners (DeepDelver home 1,
MagmaMaven home 2), so the sample-data stop is satisfied with zero data
edits and no pinned ordering can move. Update the pinned-winners table
and add boundary + sample-anchored tests; re-validate the sample via
`server.snapshot_validation.validate_snapshot`; confirm the frontend
renders the grown catalog generically (zero JS change expected).

## Close-out

- `server/views.py` (+15/−2): `HOMESTEADER_STRUCTURE = "home"` constant
  (with sample-earner note), catalog entry
  `{"id": "homesteader", "name": "Homesteader", "emoji": "🏠"}` appended
  in display order, `earned_achievements` branch (structures countMap
  read with the same isinstance-int tolerance as every other check —
  malformed structures earn nothing, never crash), and the 4-stop
  recipe note the 2026-07-11 card asked for, written next to the
  catalog tuple.
- `data/sample_snapshot.json`: UNCHANGED — chosen over Vault Lord
  precisely because the committed sample already gives Homesteader two
  clean earners (DeepDelver home 1, MagmaMaven home 2) while Vault Lord
  (vault_level == schema max 6) would have required bumping a miner's
  vault_level. Re-validated via
  `server.snapshot_validation.validate_snapshot` — passes.
- `tests/test_achievements.py` (+40/−1): catalog-ids pin grows
  `homesteader`; `HOMESTEADER_STRUCTURE` pinned in the thresholds test;
  boundary (home 1 / 2 earn, home 0 doesn't), only-home-counts,
  missing/malformed-structures tests; sample-anchored earner pin
  (DeepDelver + MagmaMaven only); `SAMPLE_WINNERS` rows updated. The
  earner-union gate passes with the grown catalog.
- `web/` — zero change, confirmed: `renderAchievements` (web/app.js
  :1433) iterates `achievements.catalog` with no hardcoded badge ids;
  tests/test_web_fun.py pins only the generic rendering seams.
- verify: `python3 -m pytest -q` → `592 passed, 1 skipped` (was 588
  + 1); `python3 bootstrap.py check --strict` → exit 0.

## 💡 Session idea

The Homesteader branch is the first badge to read `structures`, and
`earned_achievements` now unpacks five miner fields by hand
(inventory/skills/wears/equipment/structures) before the checks. If a
ninth badge lands, consider a tiny `_countmap(miner, key)` helper so
each new field is one line, not two — same tolerance, less boilerplate.
(Deduped: the 2026-07-11 card's "one-line note next to the catalog
tuple" idea is DONE in this PR, so it is retired rather than repeated.)

## ⟲ Previous-session review

The 2026-07-11-sample-data-achievement-earners card was exactly right:
its 💡 predicted the fourth mandatory stop (sample earner) and asked
for a note next to the catalog tuple. This session followed the recipe,
paid the note debt, and stress-tested the recipe's edge: stop 4 can be
satisfiable by the EXISTING sample (Homesteader needed zero data
edits), which the earner-union gate handles fine — the recipe's wording
"must gain an earner" really means "must HAVE an earner". Its
boundary-test style (earn at the line, lose one below) is reused for
the home 1/0 boundary.

- **📊 Model:** fable-5 · standard effort · task-class: 8th achievement badge — catalog + earned branch + pinned-winners tests (build)
