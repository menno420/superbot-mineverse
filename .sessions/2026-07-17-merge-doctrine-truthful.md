# Session — 2026-07-17 — Correct merge doctrine to the truth

> **Status:** `in-progress`
> **Branch:** `claude/merge-doctrine-truthful`
> **Timestamp (UTC):** Fri Jul 17 16:45:43 UTC 2026

**Owner live order (2026-07-17, verbatim):** "Please remove any mention of
'human gated' I have never and will never review an unmerged PR."

**Scope:** correct the false "owner reviews/merges unmerged PRs" doctrine to
the truth: green `claude/*` PRs auto-land via GitHub-native auto-merge (armed
by `.github/workflows/auto-merge-enabler.yml`); the owner never reviews
unmerged PRs — the owner reviews already-MERGED PRs asynchronously. Agents
still do NOT hand-arm / REST-merge; the enabler workflow arms auto-merge and
the green head SHA lands itself.

Born-red HOLD armed by this card (Status `in-progress`); the owner flips it to
complete after review of the merged PR.

- **📊 Model:** claude-opus family · task-class: docs-truth-fix
