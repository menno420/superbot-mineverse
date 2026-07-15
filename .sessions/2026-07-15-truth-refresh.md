# Session — 2026-07-15 — Truth refresh: current-state ledger + 2026-07-14 model-line advisory cleanup

> **Status:** `in-progress`
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

- **📊 Model:** fable-5 · medium · docs-only — truth refresh: living-ledger re-verification + 9-card model-line grammar normalization (records only, zero runtime change)
