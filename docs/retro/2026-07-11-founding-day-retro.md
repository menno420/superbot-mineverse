# Founding-day retrospective — 2026-07-11

> **Status:** `historical`
>
> Written at day close by the wrap-up session. This file moves the founding
> day's self-review substance out of the live `control/status.md` heartbeat
> so nothing depends on status.md git history alone. Source code and merged
> PRs always win over this narrative.

## The day in one paragraph

superbot-mineverse went from an empty repo to a shipped, owner-flag-gated
staged ladder in a single day (2026-07-11): stage 0 walking skeleton
(stdlib `http.server` + vanilla web frontend over a committed sample
snapshot), stage (a) READ contract v1 with a CI schema gate, stage (b)
Discord OAuth sign-in with degraded mode, stage (c) WRITE contract v1
(test-guild only, web side + mock shim), stage (d) live-prod cutover PREP
(owner-flag-gated, never agent-decided), then a deepening pass (full v1
field coverage in the views), an a11y/robustness pass, and an
owner-requested fun pass (cave theme, achievements, easter eggs, PNG share
card). The PR ledger ran #1–#40: 39 merged on green, 1 still open —
**PR #31**, the owner's Codex-authored pre-provisioning security report
(docs-only, not a claude/* lane). The test suite grew from 0 to
**327 passed + 1 conditional skip** (the conformance test that waits on a
real bot endpoint via `SHIM_CONFORMANCE_BASE_URL`).

## Lessons — carried out of the heartbeat

### 1. The pytest-gate saga: false alarm → probe → real gap → owner fix → empirical verification

- **False alarm, corrected:** the ORDER 000 lane flagged "substrate-gate is
  NOT a required check" after PRs #2/#3 merged seconds post-arming. A
  read-only probe DISPROVED it: main's ruleset required context
  `["substrate-gate"]` (evidence: PR #5's enable-auto-merge job read
  `rules/branches/main` server-side; PR #5 merged only after gate success).
  Flag withdrawn same hour.
- **Real gap confirmed instead:** pytest was NOT a required context — PR #10
  merged the same second its pytest run completed; PR #16 merged 28s BEFORE
  pytest finished. Routed to the owner as a click-level OWNER-ACTION.
- **Owner fix:** the owner added `pytest` as a required status check on the
  main ruleset on 2026-07-11.
- **Empirical verification method (reusable):** confirmed blocking via
  merge-timing evidence — `merged_at ≥ pytest completed_at` on PRs
  #32–#35 (merges landed 2s/2s/3s AFTER pytest completed, never before;
  contrast the pre-fix PR #16 gap). A guessed gate and a verified gate are
  different facts; verify with timestamps, not settings screenshots.

### 2. Squash merges can drop files: the .gitignore regression

PR #3's squash dropped a `.gitignore` entry, causing a recurring untracked
guard-telemetry file (`.substrate/guard-fires.jsonl`); root-caused and
re-added in follow-up PR #5. Lesson: after a squash merge, verify the merged
tree, not the branch tree.

### 3. Claim-file lifecycle held all day

Work claims (`control/claims/<slug>.md`, one file per claim) ride the
feature PR onto main and are removed by the next control-lane PR; at day
close `control/claims/` contains only its README. Single-writer file
discipline (manager owns `inbox.md`, this Project owns `status.md`, one
file per claim) produced zero merge conflicts across ~40 PRs, with one
benign rebase (slice-2 lane vs stage-(d) lane on `docs/current-state.md`,
resolved in PR #21, no loss).

### 4. ORDER 001 standing rule: model attribution

Every session card carries a family-level `📊 Model:` line (e.g. `fable-5`)
recording what the session's OWN harness reports — never a full model ID,
never a value copied from another card or read off the Routines screen
(cross-surface disagreement is evidenced fleet-wide). The rule lives in
`.sessions/README.md`; ORDER 001 (inbox) made it binding here.

### 5. Where the ORDER 002 self-review lives

The full ORDER 002 self-review text (window 2026-07-10 20:00Z →
2026-07-11 10:20Z) lives in git history: commit `4be012e` (PR #30's squash
of `control/status.md`). Its substance, preserved here so the live
heartbeat can drop it:

- Classifier denial (coordinator): spawning a worker to edit main's ruleset
  was denied by the auto-mode permission classifier ("Modify Shared
  Resources"); recorded, complied, not retried; became moot when the owner
  made the change.
- The pytest-gate false-alarm/real-gap sequence (lesson 1 above).
- The PR #3 gitignore regression (lesson 2 above).
- Merge race on `docs/current-state.md` resolved by rebase (PR #21).
- Trigger-arm error: one `create_trigger` failed "run_once_at must be in
  the future" (worker guessed the time); retried successfully; workers now
  check `date -u` first.
- Briefing drift (minor): a lane was briefed "10 unrendered-banner
  findings" when 1 remained (PR #6 took strict check RED→GREEN).
- Red CI runs on merged work: none; nothing shipped red.

(Note: the pointer previously carried in `control/status.md` cited
"PR #29 / commit 2f2d33a" — that commit is PR #29's squash, which appended
ORDER 002 to `control/inbox.md`. The review TEXT is in PR #30's squash,
commit `4be012e`.)

### 6. JS-in-CI gap (known, on the record)

The pytest suite pins SERVED BYTES only — no JavaScript executes in CI.
The Konami-code detector is therefore a small pure function
(`konamiNextProgress` in `web/app.js`), pinned structurally by
`tests/test_web_share_card.py` and verified once end-to-end in real
Chromium via Playwright during the mop-up lane (PR #40) — not on every CI
run. Already documented in the test module and the
`2026-07-11-share-card-nits` session card; any future JS with real logic
should either stay a pure function verified the same way, or bring a JS
test harness (parked on the groomed backlog).

## The numbers (verified at day close)

- PRs: #1–#40 created; 39 merged, 1 open (#31, owner's Codex security
  report).
- Tests: `python3 -m pytest -q` → **327 passed, 1 skipped**.
- Strict check: `python3 bootstrap.py check --strict` → exit 0.
- Orders: 001 and 002 acked + done.
- `control/claims/`: README only.
