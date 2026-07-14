# 2026-07-14 — substrate-kit upgrade v1.15.0 → v1.16.0

> **Status:** `complete`
> **Branch:** `claude/kit-upgrade-v1.16.0` · PR #110

- **📊 Model:** fable-5 · medium · task-class: mechanical refactor — kit-upgrade distribution wave, vendored substrate-kit v1.15.0 → v1.16.0 (kit-owned files only)

**Goal:** distribution-wave upgrade of the vendored substrate-kit from
v1.15.0 to v1.16.0 via the canonical two-command flow. Kit-owned files
only — no lane content, no `control/status.md` edits (heartbeat `kit:`
bump stays lane-owed per Q-0261.3).

## What happened

- **Vendored dist:** `bootstrap.py` replaced with the v1.16.0 release
  dist, sha256
  `bba34e2102cbaf09394f39992f0501ea5cfd542d90301ef67e31a0854ca59170`
  (980,026 bytes), three-way verified (downloaded asset == adjacent
  release.json sha256 == the wave's release fact). Outgoing v1.15.0 dist
  banked at `.substrate/backup/bootstrap-1.15.0.py` (sha256
  `25d22af9…650e`, equal to the v1.15.0 release asset); the pre-existing
  `bootstrap-1.8.0.py` bank stayed byte-identical.
- **Two-command flow, both ran:** `python3 bootstrap.py.new upgrade`
  then `python3 bootstrap.py upgrade --apply-docs`;
  `.substrate/upgrade-report.md` carries `## Applied (--apply-docs)`
  (CONSTITUTION.md, docs/collaboration-model.md, docs/SKILLS.md,
  docs/ROUTINES.md, control/claims/README.md). Report classes verbatim:
  `consumer-edited: 4 · diverged: 2 · template-improved: 5 ·
  unchanged: 14`. Capability-seed fence and seat-digest both
  "already current".
- **Check-context safety:** carve-out scan ran on both live kit-owned
  workflows — `substrate-gate.yml — ran, 0 found` and
  `auto-merge-enabler.yml — ran, 0 found`; both KEPT byte-identical, so
  the live required contexts (`substrate-gate`, `pytest`) are untouched
  by this PR.
- **New v1.16.0 plant `docs/reading-path.md`** fired BOTH a
  `[reachable]` orphan and an `[unrendered-banner]` (3 unfilled fleet
  slots) — a fresh v1.16.0 upgrade is strict-red until both are cured.
  Orphan: hand-merged the report's minimal `docs/AGENT_ORIENTATION.md`
  template hunk (read-path list line + fleet-reading paragraph) into the
  diverged orientation. Banner: answered the three slots
  (`fleet_status_command` / `fleet_dark_repos` / `fleet_siblings`,
  interview Q-014/Q-015/Q-016) with verified fleet facts (superbot
  Q-0272: hub `python3.10 scripts/fleet_status.py` orient;
  pokemon-mod-lab the only dark repo; canonical roster = superbot
  `docs/fleet-reading-path.md` + substrate-kit `docs/adopters.md`) and
  ran `bootstrap.py render --live`.
  **⚑ Decide-and-flag:** Q-014/Q-016 are user-audience slots — answered
  from the owner's own recorded doctrine rather than parked, because the
  strict gate (and hence the wave) blocks on the banner. Reversible:
  amend via `bootstrap.py answer <slot> …` + `render --live`.
- **Verify:** `python3 bootstrap.py check --strict` exit 0 / zero
  findings with the card flipped (pre-flip red = designed born-red
  hold); repo verify line `python3 -m pytest -q` = 610 passed,
  1 skipped.
- **Landing:** born-red card first commit → PR #110 opened ready →
  payload commit → this flip commit last; the repo's LIVE
  auto-merge-enabler (armed at open on `claude/*`) merges on green after
  the flip — sanctioned wave landing path, recorded here.

## Lane-owed (untouched per Q-0261.3)

- `control/status.md` heartbeat `kit:` bump to v1.16.0.
- Diverged manual merges (hunks preserved in
  `.substrate/upgrade-report.md` § Template deltas):
  `docs/AGENT_ORIENTATION.md` (rest of the delta beyond the minimal
  wiring hunk) and `docs/CAPABILITIES.md` (fleet-master-copy path case
  fix `docs/capabilities.md` → `docs/CAPABILITIES.md`).

## 💡 Session idea

The v1.16.0 `reading-path.md` plant guarantees a strict-red
`[unrendered-banner]` on every adopter whose interview hasn't answered
the three fleet slots — and two of them are user-audience, forcing wave
workers into decide-and-flag answers. Kit-side fix worth filing: ship
the plant with the banner downgraded to an advisory finding (or
pre-render the slots from the fleet registry the kit already carries in
`docs/adopters.md`), so a distribution wave never has to answer
owner-audience interview questions to go green.

## ⟲ Previous-session review

The v1.15.0 upgrade session (`.sessions/2026-07-13-kit-upgrade-v1150.md`)
was exemplary: it verified check-context safety BEFORE opening the PR and
recorded the enabler sha256 both sides — this session reused both moves
verbatim. Improvement it points at (still open): its session idea — the
carve-out scan printing `kept`/`regenerated` without pre/post sha256
pairs — remains unshipped kit-side; this session again had to hash the
workflows by hand to prove "kept" meant byte-identical.
