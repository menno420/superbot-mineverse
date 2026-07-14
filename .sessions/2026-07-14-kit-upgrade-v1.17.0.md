# 2026-07-14 — substrate-kit upgrade v1.16.0 → v1.17.0

> **Status:** `complete`
> **Branch:** `claude/kit-upgrade-v1.17.0` · PR #112

- **📊 Model:** fable-5 · medium · mechanical refactor — kit-upgrade distribution wave, vendored substrate-kit v1.16.0 → v1.17.0 (kit-owned files only)

**Goal:** distribution-wave upgrade of the vendored substrate-kit from
v1.16.0 to v1.17.0 via the canonical two-command flow. Kit-owned files
only — no lane content, no `control/status.md` edits (heartbeat `kit:`
bump stays lane-owed per Q-0261.3).

## What happened

- **Vendored dist:** `bootstrap.py` replaced with the v1.17.0 release
  dist, sha256
  `0d08b8aa9efc30178cf8e8befcfa28dd2b65e02106cc9ba6d520133017955521`
  (995,446 bytes), three-way verified (downloaded asset == adjacent
  release.json sha256 == the wave's release fact == the GitHub asset
  digest). Outgoing v1.16.0 dist banked at
  `.substrate/backup/bootstrap-1.16.0.py`; the pre-existing
  `bootstrap-1.8.0.py` and `bootstrap-1.15.0.py` banks stayed
  byte-identical (git status showed no modification).
- **Two-command flow, both ran:** `python3 bootstrap.py.new upgrade`
  then `python3 bootstrap.py upgrade --apply-docs`. The docs pass
  printed verbatim: `upgrade: apply-docs: no template-improved docs to
  apply — every planted doc is already current or consumer-owned.` —
  so this release's report has NO `## Applied (--apply-docs)` section
  by design (docs classes: 19 unchanged · 6 consumer-edited · 0
  template-improved · 0 diverged). Capability-seed fence and
  seat-digest both "already current".
- **v1.17.0 payload:** the scheduled branch-sweep workflow template,
  STAGED-only at `.substrate/ci/branch-sweep.yml` (deliberately NOT
  installed live — install is `adopt --wire-enforcement`, owner/lane
  call), plus the `branch_sweep` config knob in `substrate.config.json`
  (`branch_patterns: claude/* · codex/* · bot/*`, `cron: 17 3 * * *`).
- **Check-context safety:** carve-out scan ran on both live kit-owned
  workflows — `substrate-gate.yml — ran, 0 found` and
  `auto-merge-enabler.yml — ran, 0 found`; both KEPT, and pre/post
  sha256 pairs hashed by hand confirm byte-identical
  (`bf644599…` gate · `64f9db41…` enabler · host `schema-gate.yml`
  untouched at `d469df2e…`).
- **No strict-red this wave:** the v1.16.0 `docs/reading-path.md`
  strict-red class did NOT recur (classified `unchanged`, slots already
  rendered) — as the wave order predicted.
- **Verify:** `python3 bootstrap.py check --strict` exit 0 —
  "check: all checks passed." (advisory-only warnings). Repo verify
  `python3 -m pytest -q` = 610 passed, 1 skipped.
  `.substrate/guard-fires.jsonl` is gitignored on this repo — nothing
  to commit there.
- **Landing:** born-red card first commit (9446866) → PR #112 opened
  ready → payload commit (c209733) → this flip commit last; the repo's
  live auto-merge enabler merges on green — sanctioned wave landing
  path. Enabler preflight in the upgrade run printed UNVERIFIED
  (HTTP 403 on the settings probe — tokenless container, expected);
  the enabler's live behavior on #110 is the ground truth.

## Lane-owed (untouched per Q-0261.3)

- `control/status.md` heartbeat `kit:` bump to v1.17.0.
- Decision whether to wire the staged branch-sweep workflow live
  (`adopt --wire-enforcement`) — the plant is inert until then.

## 💡 Session idea

The upgrade engine's "kept: … (kit-owned, already current)" line for
live workflows still forces wave workers to hash the files by hand to
prove "kept" meant byte-identical (this session did it again, as did
v1.15.0 and v1.16.0). Kit-side fix worth shipping: print the pre/post
sha256 pair on every `kept:`/`regenerated:` workflow line in the
carve-out scan output and upgrade-report — one line each, turns a
manual verification step into a copy-paste proof.

## ⟲ Previous-session review

The v1.16.0 upgrade session (`.sessions/2026-07-14-kit-upgrade-v1.16.0.md`)
handled a much harder wave (guaranteed strict-red, three interview
slots, diverged-orientation hand-merge) cleanly and its card's
decide-and-flag record made this session's "did reading-path recur?"
check a ten-second grep. One improvement it surfaces: its 📊 model line
embedded `task-class:` as a literal prefix inside the class segment,
which fires the `[model-line-class]` advisory on every later check run
— this session's card drops the literal so the segment prefix-matches
`mechanical refactor`; the older card's line is lane-owed cleanup
(sibling cards are not touched mid-PR per the shadowing doctrine).
