# 2026-08-22 — the coordinator baton tells the next session to do the one banned thing

> **Status:** `in-progress` — branch `claude/correct-coordinator-baton`.
> Flips to `complete` after `python3 bootstrap.py check --strict` returns a
> real exit 0 on this tree.

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

## What this will carry when it flips

- the corrected block, and what was measured to justify each half
- the verify line with its real exit code
