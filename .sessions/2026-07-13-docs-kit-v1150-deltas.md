# Session — 2026-07-13 — kit v1.15.0 lane-owed docs deltas

> **Status:** `in-progress`
> **Branch:** `claude/docs-kit-v1150-deltas`
> **Venue:** coordinator-dispatched worker session (docs-only slice —
> the two template deltas PR #80 left lane-owed).

**Goal:** apply the kit v1.15.0 upgrade's outstanding docs deltas that
PR #80 (merged; main was `1520e05` after it) recorded as lane-owed in
`.substrate/upgrade-report.md` § "Template deltas for diverged docs":
bring `docs/CAPABILITIES.md`'s Append-log preamble to the venue-token
six-field format (the capability-seed fence itself was already refreshed
at upgrade), and apply the remaining `docs/AGENT_ORIENTATION.md`
template hunks (preflight boot section, SKILLS/ROUTINES routing
paragraphs, verify pointer) beyond the read-path list hunk #80
hand-merged. Template structure ONLY — every host-specific recorded
finding (the CAPABILITIES.md append-log ledger entries, the mineverse
contract/auth/cutover reading routes) survives verbatim.
`control/status.md`'s diverged delta is NOT in scope (one-writer file;
PR #81 already landed its kit-line fix on main `e81c9ff`).
