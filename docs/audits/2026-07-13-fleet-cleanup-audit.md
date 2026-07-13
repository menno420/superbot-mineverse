# superbot-mineverse — fleet cleanup / audit pass, 2026-07-13 night (EAP final night)

> **Status:** `audit`
>
> Complementary read-only audit pass, run alongside the owner's live
> fleet-wide dispatch ("ORDER 045: find state of all repos, dispatch
> instructions for tonight — last day of the EAP"). This is **not** a
> redispatch of work and does not touch `control/inbox.md` or
> `control/status.md` — those stay this seat's own single-writer files
> (`control/README.md` § "The two files"). Scope: verify the dispatched
> claim about this repo's state, check CI/doc health, dispose of any
> unsafe-left-open PRs, and record findings.

## What this repo is

`superbot-mineverse` is a stdlib-Python browser game/dashboard over the
live mining economy of the `menno420/superbot` Discord bot
(`README.md`). It never touches Postgres or holds the bot token; it
consumes a versioned read contract the bot projects into a relay and
(eventually) proposes writes only through a bot-side audited action
endpoint. It is on a staged ladder — stage 0 (walking skeleton) through
stage (c) (test-guild writes) are shipped; stage (d) (live-prod cutover)
is prepared but owner-flag-gated (`docs/current-state.md` § "Stability
baseline").

## Verification of the dispatched claim

The task description handed to this audit stated: *"FRESH heartbeat
about 2h45m old, all orders done, worklist reports 0 open PRs."*

That characterization traces to the EAP worklist doc's own snapshot line
— `control/inbox.md` ORDER 006 quotes the fleet-manager's worklist doc
verbatim: *"superbot-mineverse — swept @ `ae98dd0`… Honest thin list — 0
open PRs, all 5 ORDERs done."* `ae98dd0` was main HEAD at 18:49:14Z
(PR #83 merge).

**That snapshot was accurate at `ae98dd0` but stale by the time this
audit started.** This session's local clone was itself initially pinned
to `ae98dd0`; `git fetch origin` (this session, ~23:03Z) showed origin/main
had moved 5 commits ahead to `82b7caa` (PR #88, merged 2026-07-13T22:57:21Z)
— i.e. **~4 hours and 5 more merged PRs (#84–#88)** happened between the
worklist snapshot and this audit's start:

| PR | What | Merged (UTC) |
|---|---|---|
| #84 | ORDER 006 landed (EAP final-night worklist, fm ORDER 045 relay) | 22:19:15Z |
| #85 | ORDER 007 landed (owner bigger-batches/production-grade directive) + heartbeat refresh | 22:26:10Z |
| #86 | Claim-file prune (`claude-owner-order-batch-sim.md`) | 22:29:05Z |
| #87 | Claim ORDERs 006+007 for the night run + inbox-thread ack (ack placed on `status.md`, not `inbox.md` — the enforcer rejects non-append inbox edits, evidenced on run 29290416909) | 22:40:12Z |
| #88 | FLAG-1 snapshot-ingest **RECEIVE** endpoint (`POST /api/snapshot/ingest`) — ORDER 006 item 1 | 22:57:21Z |

**Re-verified live at this audit's start (23:03–23:04Z) and again
immediately before writing this report:** `mcp__github__list_pull_requests`
(state=open) returned an **empty list both times** — genuinely 0 open PRs,
matching the dispatched claim's bottom line even though the supporting
detail (which ORDERs are outstanding) had moved on.

**"All orders done" is no longer accurate as of this audit's start.**
`control/inbox.md` now carries ORDER 006 (5-item EAP worklist; item 1
shipped via #88, items 2–5 still open) and ORDER 007 (adopt
bigger-batch SIM-REQUESTs + production-grade mission — a standing
posture, not a single completable action). `control/status.md`
(`updated: 2026-07-13T22:35:08Z`) itself records `orders:
acked=001..007 done=001..005 claimed-by: 006,007 mineverse-night-runner
2026-07-13T22:35:08Z` — i.e. the seat's own heartbeat already shows
006/007 as claimed-and-in-progress, not done. This is normal, healthy,
**active** work by what is clearly a live night-runner session on this
seat (5 merges in the 43 minutes before this audit started, the last one
6 minutes before this audit's first `git fetch`) — not a problem to fix,
just a correction to the "all orders done" framing this audit was
handed. Per the audit's own ground rules, no PR here was within the
"created/updated in the last 2–3 hours" exclusion window at any point
(there were none open to touch), so this is purely a documentation
observation, not a merge/close decision.

## Open PRs — disposition

**Zero.** Verified via GitHub API (`list_pull_requests`, `state=open`)
at the start of this audit and again immediately before writing this
report — both calls returned `[]`. There was nothing to merge, close,
or flag. `control/claims/` also holds no stale claim files (only
`README.md`) — the last claim (`claude-owner-order-batch-sim.md`) was
correctly released via PR #86.

## CI setup and health

Three workflows, all kit-owned templates (`.github/workflows/`):

- **`substrate-gate.yml`** — the session-card / heartbeat / claims gate
  (born-red HOLD on an in-progress card since the kit v1.15.0 upgrade,
  PR #80 — see `docs/findings/substrate-gate-born-red-fail-open-2026-07-12.md`
  for the pre-upgrade fail-open this fixed).
- **`schema-gate.yml`** — workflow *display name* `schema-gate`, but its
  one job (and hence its check **context**) is `pytest` (`python3 -m
  pytest -q`). `docs/current-state.md` already documents this correctly;
  the outbox also records a 2026-07-13T15:08Z note asking the fleet
  registry's seat brief to stop calling this a `schema-gate` *check
  context* (there isn't one) — worth the manager applying on its next
  sweep.
- **`auto-merge-enabler.yml`** — arms native GitHub auto-merge on
  non-draft `claude/*` PRs once `substrate-gate` is a required context;
  refuses to arm if the branch-protection rule requires zero contexts
  (documented anti-footgun in the file's own header).

Live check-run sample for the last 5 PRs (#84–#88, via
`actions_list`/`list_workflow_runs`, branch=main): every completed run
is `success` except one — `substrate-gate` run 29290416909 on PR #87's
first push (head `1dd06cc3`) failed **by design**: it was the
inbox-append-grammar enforcer correctly rejecting a thread-style ACK
edit to `control/inbox.md` (quoted verbatim in the PR body and in
`control/status.md`'s `notes:` line), fixed by moving the ACK to
`status.md` on the next push (run 29290525040, success). This is the
gate working as intended, not a defect.

**Local verification (this audit, Python 3.10.20, `requirements-dev.txt`
installed):**
- `python3.10 -m pytest -q` → **575 passed, 1 skipped** (108.37s) —
  matches PR #88's own reported count exactly.
- `python3.10 bootstrap.py check --strict` → `check: all checks passed.`
  with one pre-existing, never-exit-affecting advisory
  (`owner-action-fields` — the two `⚑ needs-owner` lines in
  `control/status.md` are pointer-style, not the full six-field block;
  the full blocks do exist in `control/outbox.md`, so this is a known,
  accepted shape, not new drift).

CI is healthy: green, required-check set matches what the docs claim
(`substrate-gate` + `pytest`), and the one "failure" in the sampled
window was the gate catching a real mistake, not a flake.

## Doc quality

Documentation is unusually thorough for the repo's size (736 lines
across `README.md` + `control/{status,inbox,outbox}.md` +
`docs/current-state.md` alone, plus ~20 more docs under `docs/`).
`docs/current-state.md` is current as of this audit — its "Recently
shipped" list already includes the 2026-07-14-dated FLAG-1 entry for
PR #88, and its env-var/degraded-mode table correctly reflects the new
`MINING_SNAPSHOT_RELAY_SHARED_SECRET` requirement `POST
/api/snapshot/ingest` introduces.

One inconsistency found:

- **`docs/current-state.md` § "In flight" says "Nothing in flight. The
  founding day is wrapped and archived… remaining work is externally
  blocked."** This is stale relative to the rest of the same document
  and relative to `control/inbox.md`/`control/status.md`: ORDER 006
  items 2–5 (VERDICT 056 stale-indicator, ingest-transport spec
  addendum to `docs/mining-data-contract.md`, snapshot field-parity
  audit + shared constant, `scripts/readiness_check.py` extension) and
  ORDER 007 adoption are actively in flight per the seat's own
  heartbeat (`orders: … claimed-by: 006,007 mineverse-night-runner
  2026-07-13T22:35:08Z`, `notes: … Night runner active on the ORDER 006
  EAP worklist top-down`). Given the active merge cadence tonight this
  will likely self-correct on the next `current-state.md` touch, but it
  is a live contradiction between two committed docs as of this audit
  and worth a one-line fix on the next docs-touching PR.

Two smaller, low-priority observations (not bugs, just noted for
completeness):

- `project.index.json` (the substrate-kit AgentContextPack index) still
  holds only the kit-planted placeholder entry (`"name":
  "example-area"`, every field empty) with no corresponding
  `tools/agent_context/build_pack.py` or generated pack anywhere in the
  tree. It appears to be inert scaffolding from kit adoption that this
  repo has never populated or wired up — harmless, but worth either
  filling in or removing if the kit ever gates on it.
- `.session-journal.md` is the guidebook-only skeleton with every
  section still empty (`(Boot / run-checks / common-recovery commands
  for superbot-mineverse.)` etc.) — this repo appears to route all
  cross-session memory through `.sessions/<date>-<slug>.md` cards
  instead (19 cards on disk), which is a valid pattern, just worth
  knowing the guidebook itself carries no content yet.

## Inconsistencies / errors found (summary)

1. `docs/current-state.md` § "In flight" contradicts the same file's
   env-var table and `control/{inbox,status}.md` — see "Doc quality"
   above.
2. The registry seat brief (fleet-manager-side, not in this repo) is
   flagged by this repo's own outbox (2026-07-13T15:08Z entry) as
   still calling `schema-gate` a CI check context when the real
   context is `pytest`; unresolved as of this audit, cited here so it
   surfaces in the fleet-wide roll-up too.
3. ~30 stale `claude/*` branches remain on the remote for
   already-merged/closed PRs (e.g. `claude/cosmetic-hats`,
   `claude/js-logic-test-harness`, `claude/order-000-walking-skeleton`
   — `list_branches` sample, alphabetically truncated at 30). GitHub's
   "automatically delete head branches" repo setting does not appear to
   be enabled. Harmless (no conflict risk — branch names don't collide
   across sessions) but adds clutter to `git branch -a` / `list_branches`
   output every session has to skim past.

No PR content contradicted `main`, no open PR needed a stale-superseded
close, and no red/conflicted PR needed a mechanical fix — because there
were no open PRs at all to examine.

## Suggestions (fleet-wide or repo-local)

1. **Centralize the "is my worklist snapshot fresh?" check.** This
   audit's core finding — a dispatched "swept @ `<sha>`" snapshot going
   ~4 hours and 5 PRs stale before the next consumer reads it — is a
   structural property of any fan-out that quotes a point-in-time sweep
   into a durable `inbox.md` ORDER. A cheap fleet-wide fix: the
   worklist-authoring tooling could stamp *"verify no open PRs / no
   newer merges past `<sha>` before treating this list as current"* as
   a standing instruction inside the ORDER body itself (this repo's
   ORDER 006 already names the sweep SHA, which is what let this audit
   catch the drift — that's good practice worth generalizing to every
   seat's worklist, not just this one).
2. **Enable "automatically delete head branches" on this repo** (and
   check the other ~19 fleet repos for the same setting) — a one-click,
   reversible GitHub repo setting; owner-console-only, so an agent
   session can only recommend it, not flip it (same class of ask as the
   branch-protection asks already parked in sibling repos' outboxes).
3. **Fix the `docs/current-state.md` § "In flight" contradiction**
   (item 1 above) on this seat's next docs-touching PR — one line,
   mechanical, no judgment call needed once ORDER 006/007 are actually
   done.
4. **Either populate or delete `project.index.json`.** As shipped it's
   dead kit scaffolding (one placeholder area, zero real entries, no
   builder script in this repo). If the AgentContextPack system is
   intended for this repo eventually, populating it while the repo is
   this well-documented would be cheap; if not, deleting the placeholder
   removes a file every new session has to notice-and-discard.

## Activity note for the fleet roll-up

This repo was under **active, live coordination** for the entire audit
window: 5 PRs merged in the 43 minutes immediately before this audit's
first API call, the most recent 6 minutes prior. This audit made **no
writes to `control/inbox.md`, `control/status.md`, or
`control/claims/`** and did not open, merge, or close any PR (there were
none open) — this report is the only artifact this audit pass produces,
committed on its own branch, opened as a normal (non-draft) PR, and
**left unmerged** for the repo's own `auto-merge-enabler` / owner sweep
to land.

## Evidence index

- PRs inspected: #79–#88 (bodies + merge timestamps via
  `mcp__github__list_pull_requests`, `state=closed`).
- Live check runs: `mcp__github__actions_list` (`list_workflow_runs`,
  branch=`main`), 10 most recent as of ~23:04Z.
- Branches: `mcp__github__list_branches` (30 open `claude/*` branches
  returned, all corresponding to merged/closed PRs).
- Local verification commit: `82b7caa6851f7432719d5ac32695051d6e892843`
  (origin/main HEAD at audit time), Python 3.10.20,
  `python3.10 -m pytest -q` and `python3.10 bootstrap.py check --strict`
  run directly against the checked-out tree.
