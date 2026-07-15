# Session — 2026-07-15 — Truth refresh: current-state ledger + 2026-07-14 model-line advisory cleanup

> **Status:** `complete`
> **Branch:** `claude/truth-refresh`
> **Venue:** dispatched worker session (SuperBot World seat, truthful-records
> slice; EAP extension window per ORDER 009 — no orders served here, records
> work only).

**Goal:** two truthful-records deliverables, zero runtime change:

1. **`docs/current-state.md` truth refresh** — the living ledger was last
   touched at `0fdb1c5` (2026-07-14 01:39 +0200) and 22 commits have landed
   since (through main @ `b9ade33`): the 11-PR improvement wave (#94–#106),
   the EAP close-out audit + walkthrough (#107–#109), kit upgrades v1.16.0
   (#110) and v1.17.0 (#112), and the ORDER 009 EAP-extension note (#113).
   Every claim in the doc re-verified live at HEAD; stale ones updated,
   verified-true ones kept.
2. **Model-line advisory cleanup** — `check --strict` at baseline reports
   **17** `[model-line-*]` advisories across **9** terminal (`complete`)
   2026-07-14 cards (8 cards with `standard effort` + a
   `task-class:`-prefixed class segment; 1 card, kit-upgrade-v1.16.0, class
   segment only). Fix ONLY the `📊 Model:` line on each to the taught form
   `- **📊 Model:** <model> · <effort> · <task-class>` — family names kept
   truthful (all `fable-5`), `standard effort` normalized to the taxonomy
   value `medium`, class segments re-anchored to prefix-match a PL-004
   class with the original wording preserved after it. Not one other
   character on those cards changes; no Status badge is touched.

Baselines captured BEFORE any edit (this container, venv from
requirements-dev.txt): `python3 -m pytest -q` → **610 passed, 1 skipped in
111.69s**; `python3 bootstrap.py check --strict` → exit 0, all checks
passed, 17 model-line advisories + 1 pre-existing `[owner-action-fields]`
advisory on `control/status.md` (untouched — that file is not this
session's to write).

## Close-out

Shipped locally on `claude/truth-refresh` (base: main @ `b9ade33`), three
work-facing commits after the born-red claim+card commit `6b07974`:

- **`3ddfb02`** — the 9-card model-line normalization, exactly one line
  per card: `standard effort` → `medium` (8 cards), literal `task-class:`
  prefixes dropped and class segments re-anchored to prefix-match a
  PL-004 class (`feature build` ×4, `docs-only` ×2, `mechanical
  refactor` ×2, `test writing` ×1) with the original wording kept after
  the class. All 9 cards were `complete` before this session touched
  them; none looked live (wave closed 11/11 per #106, kit waves closed
  per their own cards) — zero skips.
- **`0d5a7a0`** — `docs/current-state.md` refresh, badge (line 3) and
  structure intact: truth-stamp added to the header blockquote (main @
  `b9ade33`, 2026-07-15); the stale born-red fail-open "known gap +
  interim rule" paragraph replaced with the verified v1.17.0 behavior —
  the added-card born-red HOLD is enforced (`BORN_RED_HOLD_MESSAGE` in
  `bootstrap.py`, and re-proven live this session: `check --strict` on
  this branch reports "HOLD (by design)" against this very card); ORDER
  009 EAP-extension posture + zero-open-PRs (API-verified) + kit-version
  self-report lag recorded under "In flight"; stale
  `control/status.md` FLAG pointers redirected to
  `docs/eap-closeout-walkthrough-2026-07-14.md` §C; four "Recently
  shipped" entries added covering #90/#94–#113; review-rhythm line made
  honest (batch refresh).
- This completion commit + the badge-flip commit close the card.

Verified pre-flip in this container (venv from requirements-dev.txt):
`python3 -m pytest -q` → **610 passed, 1 skipped in 110.91s** (records-only
diff, zero test deltas as predicted); `python3 bootstrap.py check
--strict` → model-line advisories **17 → 0**; remaining findings are
exactly the designed born-red hold on this card (flipped by the next
commit) and the pre-existing `[owner-action-fields]` advisory on
`control/status.md` (not this session's file to write — one writer per
file).

NOTE (venue): this session was scope-changed mid-run by its coordinator —
push and PR creation withheld (platform-side classifier denying
dispatched-session pushes), so the branch is completed and verified
locally; it lands via PR when the lane's push path reopens.

## 💡 Session idea

The 17-advisory pile this session mopped up was born in ONE night by ONE
wave (8 improvement-wave cards, same two defects: `standard effort` + a
literal `task-class:` prefix), and the v1.17.0 kit-upgrade card even
*diagnosed* the defect in its previous-session review while deferring the
sibling fix as "lane-owed cleanup" — which cost this whole follow-up
session. The cheap enforcing fix is upstream at flip time, not in more
sweeps: the kit's session-close path already parses the closing card's 📊
payload (`loop.telemetry` harvest), so make session-close surface the
taught-form fix inline — or refuse the flip draft — when the card being
flipped carries an off-taxonomy effort or non-prefix-matching class; at
flip time it is a 5-second self-edit, a night later it is a 9-card
archaeology session. Dedup checked: the kit's own
`model-line-payload-lint-advisory-2026-07-11` idea shipped the
*check-time* advisory this session consumed; no mineverse card or
`docs/ideas/` entry proposes moving that lint to the *flip gate* (the
verdict-056 card's 💡 is staleness-constant parity, the v1.17.0 card's 💡
is sha256 pairs on upgrade output).

## ⟲ Previous-session review

The `2026-07-14-kit-upgrade-v1.17.0` card (newest prior card, #112) is a
strong wave record: three-way sha256 verification of the vendored dist
and by-hand pre/post workflow hashes make "kept meant byte-identical"
checkable rather than asserted, and its 💡 (print the sha256 pair on
every `kept:` line) is the right friction→guard shape for exactly the
step it had to repeat. Two honest nits, one of which priced this session:
(a) its review correctly diagnosed the `task-class:`-literal defect on
the v1.16.0 sibling card but deferred the one-line fix as "lane-owed
cleanup" — correctly per the shadowing doctrine, yet nothing scheduled
the cleanup, so the pile sat until this dedicated session; a guard recipe
naming the affected cards would have turned this session's scan into a
lookup. (b) Its own 📊 line was that night's only clean one, which is
evidence the defect class is a flip-time gate gap, not an education gap.

- **📊 Model:** fable-5 · medium · docs-only — truth refresh: living-ledger re-verification + 9-card model-line grammar normalization (records only, zero runtime change)
