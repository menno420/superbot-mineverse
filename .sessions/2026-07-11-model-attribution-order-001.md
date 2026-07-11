# Session 2026-07-11 — ORDER 001: model-attribution line on session cards

> **Status:** `complete`

## Plan

Execute inbox ORDER 001 (model-attribution ground truth, family-level
names only per fleet Q-0262):

1. **Confirm the card template carries `📊 Model:`** — locate the
   session-card scaffold and verify the line exists; add it if missing.
2. **Document the standing rule** where the session-log practice lives
   (`.sessions/README.md`): every fired session records the model family
   its *own* harness reports, family-level name only — never the full
   model ID, never a value copied from another card or from the
   Routines screen.
3. **Prove it on this session's own card** — this file carries a real
   family-level `📊 Model:` line (the done-when condition).

Constraints honored: docs-only diff; `control/inbox.md` and
`control/status.md` untouched (coordinator-owned); no code changes.

## Close-out

- **Template: already compliant, no code change needed.** The card
  scaffold is the kit auto-drafter in `bootstrap.py` (`_marker_line`,
  "Model line" branch) — it already emits
  `- **📊 Model:** [[fill: model]] · [[fill: effort]] · [[fill: task-class]]`,
  and the marker is declared in `substrate.config.json` →
  `session_markers` (needle `📊 Model:`). Confirmed present; nothing to
  add.
- `.sessions/README.md`: added the standing-rule paragraph — the
  `📊 Model:` value is the family-level name the session's own
  harness/environment reports (e.g. `fable-5`), never the full model ID
  string and never copied from another card or an external surface; the
  Routines screen is NOT reliable attribution (evidence: fleet model
  matrix, websites PR #59 cross-surface disagreement).
- This card is the ORDER 001 done-when artifact: its Model line below
  records the family my own harness reports.
- verify: `python3 bootstrap.py check --strict` and
  `python3 -m pytest -q` — results recorded in the PR body.

## 💡 Session idea

The check gate scans for the `📊 Model:` needle but cannot tell a
family-level name (`fable-5`) from a full model ID or a placeholder like
"(identifier withheld)". A tiny advisory in the model-line parser — flag
values matching `claude-*`/`us.anthropic.*` or containing "withheld" —
would make the family-level standing rule self-enforcing instead of
README-enforced.

## ⟲ Previous-session review

The micro-polish-identity-xp card demonstrates exactly why ORDER 001
exists: its Model line reads "(identifier withheld this session)" — the
marker scan passes but the PL-004 row carries no usable attribution.
Earlier cards also drift across three spellings for the same family
("Claude Fable 5", "claude-fable-5", "claude"). The README rule added
this session gives future cards one canonical form; the enforcement
advisory is deferred (see session idea above) since this slice is
docs-only by order scope.

- **📊 Model:** fable-5 · standard effort · docs-only
