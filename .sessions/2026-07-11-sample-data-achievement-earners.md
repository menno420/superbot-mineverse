# Session 2026-07-11 — sample data: every achievement gets an earner

> **Status:** `complete`

## Plan

Fun mop-up slice, data side (the sibling PR handles web/ polish; this
PR touches NO web/ files so the two cannot conflict). The achievements
panel shipped by the fun layer (PR #37) has two badges the committed
sample can never light up — Fully Geared and Tool Breaker were honest
zero-states. Enrich `data/sample_snapshot.json` with two new miners so
EVERY catalog badge has at least one live earner, without moving any
existing miner or breaking the pinned leaderboard/minimap orderings.
No schema/contract change; payload stays v1-conformant.

## Close-out

- `data/sample_snapshot.json` (+36): two new miners, both placed to
  dodge every pinned ordering (depth ≠ 3, coins strictly between
  PebblePicker's 480 and MagmaMaven's 25 990, level < 16):
  - **GearGoblin** (suid …006, depth 2): all 9 schema equipment slots
    filled → earns *Fully Geared* and only that (skills spread 2, pack
    95, coins 5 620, wear ≤ 26 keep every other badge off).
  - **RustyRelic** (suid …007, depth 1): battered pickaxe at 117 wear,
    over the 100 display cap → earns *Tool Breaker* and only that
    (2 slots equipped, 1 skill, pack 95, no 42-count item).
- `server/views.py` (comment only): the TOOL_BREAKER_WEAR note no
  longer claims "no sample miner is there yet" — it names RustyRelic.
- `tests/test_achievements.py` (+63/−10): the two zero-state pins
  (`test_no_sample_miner_is_fully_geared`, `test_no_sample_miner_broke_a_tool`)
  DELIBERATELY inverted into only-earner pins — the zero-state was the
  documented sample fact this PR exists to change. New boundary tests
  anchored to the committed miners: GearGoblin fills exactly the 9
  schema slots and emptying ANY one slot loses the badge; RustyRelic's
  max wear ≥ the cap and clamping every wear to cap−1 loses the badge;
  `SAMPLE_WINNERS` extended with the two new rows; new
  `test_every_catalog_achievement_has_a_sample_earner` pins the demo
  guarantee (earned-union == catalog ids) so a future badge cannot land
  earner-less unnoticed.
- verify: `python3 bootstrap.py check --strict` → `check: all checks
  passed.`; `python3 -m pytest -q` → `319 passed, 1 skipped` (was 314
  + 1).

## 💡 Session idea

`ACHIEVEMENT_CATALOG` grows by editing `server/views.py` in three
places (constant, catalog tuple, `earned_achievements` branch). The new
`test_every_catalog_achievement_has_a_sample_earner` now makes a fourth
mandatory stop: `data/sample_snapshot.json` must gain an earner in the
same PR. Worth a one-line note next to the catalog tuple so the next
badge author finds the rule before red CI does.

## ⟲ Previous-session review

The 2026-07-11-fun-layer card pinned the sample winners table and
explicitly called out Fully Geared / Tool Breaker as honest zero-states
("No sample miner is there yet"). This session is the planned follow-up
that retires those zero-states with data instead of loosening
thresholds — its boundary-test style (earn at the line, lose one below)
is reused verbatim for the two new sample-anchored tests.

- **📊 Model:** Fable · standard effort · task-class: sample-data enrichment + tests (build)
