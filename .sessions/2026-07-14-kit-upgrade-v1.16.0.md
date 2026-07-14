# 2026-07-14 — substrate-kit upgrade v1.15.0 → v1.16.0

> **Status:** `in-progress`
> **Branch:** `claude/kit-upgrade-v1.16.0`

- **📊 Model:** fable-5 · standard effort · task-class: kit-upgrade distribution wave — vendored substrate-kit v1.15.0 → v1.16.0 (kit-owned files only)

**Goal:** distribution-wave upgrade of the vendored substrate-kit from
v1.15.0 to v1.16.0 via the canonical two-command flow
(`python3 bootstrap.py.new upgrade`, then
`python3 bootstrap.py upgrade --apply-docs`). Kit-owned files only —
no lane content, no `control/status.md` edits (heartbeat `kit:` bump
stays lane-owed per Q-0261.3). Landing: born-red card first commit,
work batched, flip `complete` last; the repo's live auto-merge-enabler
merges on green after the flip (sanctioned, recorded here).
