# SuperBot World seat heartbeat · 2026-07-16T15:59Z · pacemaker recovery + ORDER 010 investigated
updated: 2026-07-16T15:59:00Z
phase: pacemaker recovery — the coordinator's send_later chain stalled ~08:45Z→11:15Z (armed link vanished without firing), re-armed at 11:18Z and has run clean since; ORDER 010 (mirror idle PR #142) investigated and closed N/A with citation below; landing blocked this session by a GitHub-access wall (see BLOCKER).
health: green (repo/tests unchanged from last verified stamp) — landing capability is the open issue, not repo health
kit: v1.17.0 · check: not re-run this stamp (no code touched — investigation + control-doc only)
last-shipped: none this session — see BLOCKER; this stamp + the ORDER 010 disposition are prepared on branch `claude/order-010-mirror-142-na` (pushed, PR NOT opened — see below)
blockers: **BLOCKER — GitHub PR-creation is unavailable this session.** Verified three times over ~5h (11:15Z, 13:15Z, 15:59Z): `api.github.com` direct HTTP → `{"message":"GitHub access is not enabled for this session. An org admin must connect the Claude GitHub App for this organization."}` even after `add_repo` grants git-clone scope (tested live against this repo, see docs/CAPABILITIES.md append). No `gh` CLI on PATH. `ListConnectors`/`ToolSearch` show zero GitHub MCP tools loaded this session — the path docs/CAPABILITIES.md names ("GitHub MCP tools are the path") does not exist in this venue. Plain `git` clone/fetch/push over HTTPS DOES work (proxied, credentialed) — read + branch-push are fine, only PR-open/merge is blocked. Net effect: nothing can land (even control-only heartbeat commits) until an org admin connects the GitHub App for this session's venue, or a future session finds a working GitHub MCP tool set.
orders: acked=001-010 done=001-008,010(N/A) — 009 acked-not-relisted-done here (see prior stamp; unaffected by this session)
⚑ needs-owner: (1) unchanged EAP-closeout clicks, docs/eap-closeout-walkthrough-2026-07-14.md §C (incl. OA-003); (2) **NEW, P1** — connect/reconnect the Claude GitHub App for this session's org/venue so PR-creation works again; every seat's landing path is blocked fleet-wide until this is clicked (verified from the mineverse seat, likely applies fleet-wide — re-verify per repo per the fleet-coordination-protocol before assuming).
notes: this stamp itself cannot land this session for the same reason — it is written to the working tree and pushed to `claude/order-010-mirror-142-na`, but no PR could be opened. Whoever restores GitHub access (owner, or a session with working GitHub MCP tools) should open the PR from that branch; the content is ready and tested (doc-only diff, no CI risk).

## ORDER 010 — mirror idle PR #142 reconcile-race fix — CLOSED N/A

Investigated per the ORDER's own done-when clause ("if it does not apply, record why and close N/A"):

- Idle PR #142 (`ddc59a0` on `menno420/superbot-idle`, fetched via
  `refs/pull/142/head`) fixes a TOCTOU race **inside
  `.github/workflows/automerge-card-guard.yml`**: its provenance-stamp step
  calls `gh pr merge --disable-auto` to disarm auto-merge before re-arming
  with a `Head-ref:` trailer; the fix makes that disarm call
  `fatal=False` and, on failure, checks live whether auto-merge already
  landed the PR in the race window (skip quietly) vs. genuinely failed
  (warn, leave the enabler's arm standing).
- **superbot-mineverse has no `automerge-card-guard.yml` and no
  provenance-stamp/`Head-ref` step anywhere** (`grep -rl "Head-ref\|
  provenance stamp\|card-guard" .github .substrate` → zero hits). This
  repo's only merge-automation file is `.github/workflows/auto-merge-enabler.yml`,
  which just arms `gh pr merge --auto --squash` once at PR-open/synchronize
  and never calls `--disable-auto` — the specific TOCTOU window #142 closes
  does not exist here because the vulnerable code path was never adopted.
  `grep -rn "reconcile"` across non-vendored files (excluding
  `bootstrap.py`/`.substrate/backup/*`, which are kit-vendored) returns
  nothing either.
- **Disposition: N/A** — nothing to port; no equivalent race exists in this
  repo's architecture. Recorded here per the ORDER's done-when.

## REPO STATE (live main shas at stamp)

- mineverse `21b89a0` green (unchanged from last verified pytest run @141373d;
  this session only added the fleet-manager ORDER 010 dispatch commit,
  no product code)
- games / idle — not re-verified this stamp (prior stamp: games `5db902a`
  810 passed, idle `25d34f1` 1381 passed + 1 skipped — see prior heartbeat
  in git history for full citations)

## ROUTINES (neutral facts)

- Failsafe `trig_01B32hfwxfA67orKfBzQVdmU` · "SuperBot World failsafe wake" ·
  cron `15 1-23/2 * * *` · bound to this coordinator session; found the
  pacemaker chain STALLED at the 11:15Z wake (last fire 08:45Z, the armed
  10:47Z link had vanished from `list_triggers` entirely — not fired, not
  listed); re-armed 11:18Z and has fired clean on a ~20min cadence since
  (verified at every subsequent tick through 15:59Z).
- No duplicate/predecessor failsafe trigger found for this seat at any
  check this session (contra an unverified cross-session claim received
  at 01:15Z alleging a duplicate — that claim's own sender-ID was
  self-referential and did not match live trigger data; disregarded, see
  session transcript).

## NEXT-2 BATON

1. **Owner: reconnect the GitHub App** for this session's venue — blocks
   all landing fleet-wide until clicked (see BLOCKER above).
2. Once landing works again: open the PR from `claude/order-010-mirror-142-na`
   (this stamp + ORDER 010 N/A disposition, doc-only) and re-verify games/idle
   REPO STATE live (this stamp only re-verified mineverse).
