# 2026-07-14 — substrate-kit upgrade v1.16.0 → v1.17.0

> **Status:** `in-progress`
> **Branch:** `claude/kit-upgrade-v1.17.0`

- **📊 Model:** fable-5 · medium · mechanical refactor — kit-upgrade distribution wave, vendored substrate-kit v1.16.0 → v1.17.0 (kit-owned files only)

**Goal:** distribution-wave upgrade of the vendored substrate-kit from
v1.16.0 to v1.17.0 via the canonical two-command flow. Kit-owned files
only — no lane content, no `control/status.md` edits (heartbeat `kit:`
bump stays lane-owed per Q-0261.3).

## What is about to happen

Replace the vendored `bootstrap.py` with the sha256-verified v1.17.0
release dist, run `upgrade` + `upgrade --apply-docs`, verify the live
kit-owned workflows stay byte-identical, keep the new branch-sweep
workflow STAGED-only (`.substrate/ci/branch-sweep.yml`), gate with
`check --strict`, ship as this PR.
