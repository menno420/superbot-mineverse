# Session 2026-07-11 — housekeeping: model-name normalization + current-state refresh

> **Status:** `complete`

## Plan

Two-part housekeeping slice (the ORDER 001 close-out's flagged follow-up:
"older cards carry drifted model spellings"):

1. **Normalize `📊 Model:` spellings in `.sessions/`** to the family-level
   canonical form per the standing rule in `.sessions/README.md`
   (e.g. `fable-5`) — spelling/format only, NEVER changing which model
   family a card attributes. Cards that claim no family at all are left
   untouched rather than invented.
2. **Full refresh of `docs/current-state.md`** — the placeholder-heavy
   ledger rewritten to reflect what is true now: the shipped ladder
   (0/a/b/c done, d prepared + owner-flag-gated), the read/write contract
   schemas, the degraded-by-default posture (six env-var NAMES only), CI
   (substrate-gate + pytest both required on main), and the externally
   pending items (bot-lane FLAGs 1+2, owner env vars, stage-(d) flag).

Constraints honored: docs-only diff; `control/status.md` /
`control/inbox.md` untouched; no code, schema, or contract changes.

## Close-out

- **10 cards normalized**, all attribution-preserving: nine
  `Claude Fable 5` → `fable-5` (conformance-env-seam,
  deep-views-slice2, discord-oauth, enforce-pytest-gate,
  live-prod-cutover, read-contract-v1, read-views-deepening,
  write-contract-v1, write-ui-shim-v1) and one `claude-fable-5` →
  `fable-5` (interview-slots-readme).
- **2 cards deliberately untouched**: `2026-07-11-session.md`
  (`claude` — no family claimed; normalizing would attribute one) and
  `2026-07-11-micro-polish-identity-xp.md` (`(identifier withheld this
  session)` — same reason). Both remain honest as-is under the standing
  rule; only a session's own self-report may fill them.
- `docs/current-state.md` rewritten (stability baseline = shipped ladder,
  verified against `schemas/`, `server/`, `web/`, `tests/`,
  `.github/workflows/`; the pytest job in `schema-gate.yml` is the
  `pytest` required context). Externally-pending section points at the
  two bot-lane FLAGs in `control/status.md` verbatim by name.
- `control/claims/`: no claim file corresponds to this slice (directory
  holds only its README) — nothing to remove.
- verify: `python3 bootstrap.py check --strict` and
  `python3 -m pytest -q` — both green before push; tails recorded in
  the PR report.

## 💡 Session idea

The ORDER 001 card already proposed the self-enforcing advisory (flag
`claude-*` / `us.anthropic.*` / "withheld" values in the model-line
parser). After this normalization pass the repo is at a clean baseline —
landing that advisory NOW would keep it clean for free, before new drift
accumulates. Guard recipe: model-line scan lives with the
`session_markers` needle handling in `bootstrap.py` (needle `📊 Model:`,
declared in `substrate.config.json`); test target alongside the existing
check-gate tests.

## ⟲ Previous-session review

The model-attribution-order-001 card did exactly what a good order slice
should: it fixed the rule (README), proved it on its own card, and
flagged — but did not scope-creep into — the historical drift this
session cleaned up. Its enumeration of the three drifted spellings
("Claude Fable 5", "claude-fable-5", "claude") matched what the grep
found, which made this slice mechanical. One nuance it under-called: two
cards carry no family at all, and the standing rule gives no retroactive
fill path — noted above as deliberately untouched.

- **📊 Model:** fable-5 · standard effort · task-class: housekeeping (session-card normalization + status-ledger refresh, docs-only)
