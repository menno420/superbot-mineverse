# 2026-08-22 — the coordinator baton tells the next session to do the one banned thing

> **Status:** `complete` — branch `claude/correct-coordinator-baton`, PR #145.
> Flipped after `python3 bootstrap.py check --strict` returned a real exit 0 on
> this tree, read directly and never after a pipe.

- **📊 Model:** opus-5 · high · docs-only

## 💡 Session idea

`docs/current-state.md` § *Coordinator baton* instructs the next session to
**delete a trigger**. That is the single action the estate forbids outright: it
raises an approval prompt on the owner's screen in automode and the session then
stalls until he is physically back to click it, unable to see that it is
waiting. The instruction is also **stale** — the trigger it names no longer
exists on the account.

This repo is archive-bound under the estate's 2026-08-22 disposition pass, and
an archived repository is read-only. This document is the **SuperBot-World fleet
MASTER** that the games and idle repos route their fleet-wide threads to, so
archiving it as-is would seal a forbidden instruction, permanently readable, into
the one document the whole family points at. The correction has to land first.

Scope: this one block. No code, no behaviour, no archiving — the archive
decision is the owner's and is not taken here.

## previous-session review

The previous card (`2026-08-13-kit-upgrade-v1.21.0.md`) took the kit to v1.21.0
and left the staged web app parked. Nothing it recorded touches this block, and
nothing it recorded is contradicted here — the baton predates it by a month and
survived that pass unread, which is the point: a stale instruction in a
living-ledger doc is invisible to work that has no reason to open that section.

## What landed

The baton's first bullet is **struck through and corrected in place** — the
estate era-banners seat-era material rather than erasing it, so the historical
handoff survives beside the correction. The block header now reads HISTORICAL.
The two remaining bullets are harmless July facts and were not touched.

The correction gives two independent reasons, either one sufficient:

1. **Never delete a trigger** (D-0015). Disabling is the emergency stop —
   `update_trigger` with `enabled: false`: no prompt, reversible. If removal is
   genuinely needed, say so in the reply; he does it in seconds.
2. **The named trigger no longer exists.** `MEASURED` 2026-08-22 against the
   account's Routine list — three Routines, none of them `trig_01XJJ88…`. A
   cron Routine is not a kind a default listing hides, so absence is real.

## What was checked, not assumed

- **The blast radius.** Both siblings (`superbot-games`, `superbot-idle`) were
  searched for the same instruction in their `current-state.md` and
  `PROJECT-CLOSEOUT.md`: **zero hits**. This was the family's only instance, so
  no follow-on PR is owed.
- **The pre-existing red.** `check --strict` on `main` returns **exit 0** while
  still printing `[boot-section-missing]` for `.claude/CLAUDE.md` — so that
  finding is advisory on both sides, not something this branch introduced and
  not this PR's to fix. Naming it here so the next session does not re-derive it.
- **Orientation budget.** This repo gates the boot read path at 7,000 words;
  the edit moved it 4,717 → 4,942, leaving 2,058 words of headroom. Checked
  before writing, because the hub is currently at zero headroom and that is
  the failure worth not repeating.

## Why a parked repo was worth a PR

This document is the **SuperBot-World fleet MASTER** — games and idle route
their fleet-wide threads here — and the repo is archive-bound under the
2026-08-22 disposition pass. Archiving is read-only, so sealing it as-is would
have frozen a forbidden instruction, permanently readable, into the one document
the whole family points at. The general rule this instance belongs to: **anything
a repository still needs written has to be written before it is archived** —
GitHub's own archiving guidance recommends the same order for issues, PRs and
the README.

Nothing here archives anything. That decision is the owner's.

## Verify

`python3 bootstrap.py check --strict` → **exit 0**, read directly. Before the
flip it returned 1 on the designed born-red hold alone.
