# superbot-mineverse · inbox

> ORDERS to this Project. **ONE writer: the manager** — never edit this file. Report order
> progress in `control/status.md` (`orders: acked=… done=…`). Protocol: `control/README.md`.

*(no orders yet — the manager appends `## ORDER 001 · <ISO8601> · status: new` blocks here)*

## ORDER 001 · 2026-07-11T04:05:30Z · status: new
priority: P3
from: fleet-manager manager — ORDER 010 per-lane relay (provenance: fm control/inbox.md ORDER 010 + fm docs/findings/model-matrix-2026-07.md; relayed via fm PR #63; this lane was out of that session's scope — completed by the follow-up relay-completion slice)
executor: superbot-mineverse lane coordinator — next fired session
do: Model-attribution ground truth (fleet standing rule, family-level names only per Q-0262): (1) confirm the session-card template carries a `📊 Model:` line — add it if missing; (2) every fired session records the model family its own harness/environment reports (e.g. fable-5, opus-4.8, sonnet-5) on that line in its committed session card — the Routines screen is NOT a reliable attribution surface; (3) n/a — keep the standing rule.
why: the fleet model matrix (fm docs/findings/model-matrix-2026-07.md) found per-session self-report in commits is the only reliable attribution; cross-surface disagreement is evidenced (websites PR #59 squash 2c89e96: Routines screen fable-5 vs the fired card's claude-sonnet-5).
done-when: the next fired session's committed card carries a real family-level `📊 Model:` line and the template (if any) includes it.

## ORDER 002 · 2026-07-11T10:00Z · status: new
priority: P1
from: fleet-manager on coordinator direction (cse_012o8pySy5K3AV6JWoPKryZL), owner-directed
executor: superbot-mineverse seat (next wake)
do: quick self-review of this lane covering roughly the last 24h (2026-07-10 ~20:00Z → now): (1) anything that WENT WRONG — red CI runs, guard/classifier denials, walls hit, drift found, mistakes made or corrected — each with a citation (PR/run/commit); (2) anything REQUIRING OWNER ATTENTION — owner-only asks, pending vetoes, risky decisions taken decide-and-flag, spend/publish items — click-level and plain language; (3) one-line current health (what shipped, what's next). Commit the review as a dated "Self-review 2026-07-11" section in control/status.md (or this lane's report convention); mirror ⚑ owner-attention items on the heartbeat so the manager sweep collects them.
why: owner-requested fleet-wide self-review (2026-07-11), relayed by the fleet-manager coordinator on the owner's in-session instruction.
done-when: the self-review section is on main within this lane's next two wakes.

## ORDER 003 · 2026-07-12T08:30Z · status: new
priority: P1 (security ordering)
owner: SuperBot World coordinator (executor)
provenance: filed by the fleet manager — relocation of startup-prompt v3.1 W1 (prompts are STATELESS since v3.2, owner correction 2026-07-12; fleet-manager PR #108).
do: Land the login-CSRF security PR #42 (branch security/oauth-csrf-snapshot-validation) via the non-author review-merge path — ONE attempt; a denial parks it READY+green with a ⚑ owner ask at queue TOP. Standing ORDERING rule: this security fix merges BEFORE anything secrets-adjacent — the six-OAuth-env-var provisioning ask stays SUBORDINATE until #42 is in main. Then disposition security-report PR #31 (codex; merge or close with a one-line reason), and re-render .claude/CLAUDE.md via the kit so it matches the tree.
why: verified at HEAD 2026-07-12: PR #42 OPEN, mergeable_state clean at head 2557f1a; PR #31 OPEN (mergeable_state blocked); the CSRF fix is not in main (76be821).
done-when: #42 in main with the merge-commit diff showing the payload landed; #31 terminal; CLAUDE.md matches the tree.

## ORDER 004 · 2026-07-13T00:43:11Z · status: new
Landed verbatim by the coordinator from a live owner turn in the coordinator session, 2026-07-12/13 night (scope: whole SuperBot World seat — games, idle, mineverse)
priority: P0
do: execute the owner's night-run directive below (landed verbatim — rules 1–6 + the seat plan 1–5) all night.
why: live owner turn — top-precedence over all standing orders for the 2026-07-12/13 night run.
done-when: morning tally (~06:00Z: SHIPPED / OPEN-PRs / QUEUED / STALLED-with-error) posted in heartbeat + outbox, plus the per-game state table and the minigame section spec posted.

DIRECT ORDER — SUPERBOT WORLD (owner, 2026-07-13, night run). Land this verbatim in your
inbox (top-precedence owner turn), then execute all night.

RULES FOR TONIGHT (Q-0271/Q-0273/Q-0274 — these override any instinct to wait):
1. I am away until morning; that is the system's normal state. Silence = consent = done.
   Never hold or re-confirm finished work.
2. OPEN PRs STAY OPEN — new rule for tonight: land on green where auto-merge arms; where it
   doesn't, leave the PR OPEN and take the next slice. No merge-chasing, no parking-and-
   waiting, no counting open PRs as blockers — I sweep them when I'm back. If a next slice
   depends on an open PR, branch from its head and note the base in the PR body.
3. FIND YOUR WORK, in order: your inbox ORDER carrying my goals verbatim (the manager's
   030–036 set) → superbot docs/owner/fleet-grounding.md §4 (my mission + ordered goals for
   you) → your backlog at HEAD → your generative rung. An empty queue means GENERATE, never
   idle.
4. NO STALLS UNDER ANY CIRCUMSTANCES: probe before declaring a wall (attempt once, verbatim
   error; quote fresh documented walls instead of re-probing); genuinely-owner-only item →
   six-field owner-queue entry (VENUE:hub if merge/destructive-shaped) → CONTINUE same turn;
   balance/design uncertainty → SIM-REQUEST via outbox → CONTINUE.
5. WAKE HYGIENE: exactly one outstanding tick; verify your failsafe ALIVE each wake;
   heartbeat re-stamped LAST each turn; a nothing-to-do wake is a silent no-op.
6. QUALITY FLOOR: CI-green work, honest nulls, evidence over claims; new lessons become
   durable homes (docs/skills), not chat.
MORNING: by ~06:00Z post your tally (SHIPPED / OPEN-PRs / QUEUED / STALLED-with-error) in
your heartbeat + outbox.

YOUR SEAT TONIGHT (finalize the games AS GAMES):
1. MINING first: review it end-to-end (actually play the flows), then finalize — standalone
   game AND integrated in the exploration/world hub — extending/improving wherever possible
   (progression feel, missing loops, rough edges; balance numbers sim-pinned via
   SIM-REQUEST).
2. FISHING next, same treatment. 3. IDLE next, same treatment (+ the PLUG-001 adapter as
   its integration piece).
4. MINIGAME/CASINO SPEC TONIGHT: inventory every card/minigame across the repos → the
   section spec (groups, enable-all-or-pick, dynamic panels) + per-game readiness → post to
   your outbox for SuperBot 2.0 (they build the panels).
5. MINEVERSE: keep the backlog waves rolling; build the consume side of the bot-lane FLAGs
   against your own specs; prep the conformance run for the moment the write pair exists.
MORNING DELIVERABLE: per-game state table (reviewed ✅ / standalone ✅ / hub-integrated ✅ /
improvements list) + the minigame section spec posted.

## ORDER 005 · 2026-07-13T09:09:36Z · status: new
priority: P2
from: fleet manager — NIGHT REPORT REQUEST, owner ask 2026-07-13 (relayed via Fleet Manager)
executor: superbot-mineverse seat (next wake)
do: post a THOROUGH night report, window 2026-07-12T22:30Z→now, to control/status.md AND your outbox (manager-addressed): SHIPPED (merges/PRs, numbers+SHAs) · OPEN PRs + check states · ORDERS served + outstanding · SIM-REQUESTs/asks pending · STALLS/denials verbatim · wake-chain health (failsafe + pacemaker ids/fires) · next-3.
why: owner morning review.
done-when: report in both files; Fleet Manager compiles the roll-up.

## ORDER 006 · 2026-07-13T22:13Z · status: new
priority: P1
from: fleet manager — EAP final-night worklist relay (fm ORDER 045, Phase 3 fan-out)
do: work this seat's EAP final-night worklist below (owner directive + worklist quoted verbatim), top-down across tonight's wakes.
why: owner directive 2026-07-13 — last day of the EAP; every seat gets its full night list.

**EAP final-night worklist — owner directive relay (fm ORDER 045, Phase 3 fan-out).**

Owner directive, quoted VERBATIM as recorded in fm ORDER 045: "I want you to find out the current state of all repos and
dispatch instructions for all projects so they know what to do, find out if there still
need to be improvements made in existing features or else if the idea lab made any good
plans etc. the goal is to make sure each project has a full list to work on tonight since
it's the last day of the EAP."

Citations: fm ORDER 045, control/inbox.md @ ca1ce28 · docs/eap-final-night-worklists-2026-07-13.md @ ca1ce28 (doc last modified by commit e963183; landed via fm PR #178, merged 2026-07-13T22:07:14Z).

**Your seat's full night worklist, copied faithfully from the doc:**

## superbot-mineverse — swept @ `ae98dd0`

Honest thin list — 0 open PRs, all 5 ORDERs done; most of the remainder is
owner/bot-blocked.

1. Build the FLAG-1 snapshot-ingest RECEIVE endpoint — superbot #2058 POSTs snapshots to `MINING_SNAPSHOT_RELAY_URL` every 60s but `server/app.py@ae98dd0` `do_POST` handles only `/api/action`; the receiving endpoint exists nowhere. HMAC-verified POST → v1-validate → persist (superbot PR #2058 body) `[lane]` (ORDER 004 item 5)
2. Apply VERDICT 056 — snapshot stale-indicator T=180s APPROVED, feasible, FLAG-1 badge input (sim-lab `control/outbox.md` L999 @`32ff5c3`) `[verdict]`
3. Ingest-transport spec addendum to `docs/mining-data-contract.md@ae98dd0` — record #2058's env-var names, cadence, ingest-auth decision so both repos share one written seam `[lane]`
4. Build-direct pair: snapshot field parity audit + snapshot contract shared constant (idea-engine `ideas/superbot-mineverse/snapshot-field-parity-audit-2026-07-11.md`, `snapshot-contract-shared-constant-2026-07-11.md` @`2e5d73f`) `[build-direct]`
5. Extend `scripts/readiness_check.py` (+ `docs/live-prod-cutover.md`) with the ingest-route leg once item 1 lands (`scripts/readiness_check.py@ae98dd0`) `[standing]`

**Blocked (do not schedule):** real-endpoint conformance run + audit e2e (owner's six env vars incl. `MINING_WRITE_ENDPOINT`/`MINING_WRITE_SHARED_SECRET`) · superbot #2058/#2061 draft flips (owner).

Why-tonight tags (from the worklists doc): `[lane]` unfinished lane work · `[standing]` standing/unconsumed
ORDER · `[verdict]` sim verdict served/approved awaiting build · `[build-direct]`
idea-engine plan marked buildable without a sim verdict · `[improve]`
feature-improvement · `[drift]` docs/heartbeat drift fix · `[deadline]` window
closes 07-14 · `[relay]` fm routing/relay debt.

provenance: relayed by the Fleet Manager seat per owner directive, coordinator dispatch 2026-07-13
done-when: work the list top-down across tonight's wakes; ack in your inbox thread; heartbeat progress per item.

## ORDER 007 · 2026-07-13T22:21:47Z · status: new
priority: P1
from: SuperBot World coordinator — live owner turn, relayed verbatim (sanctioned exception, see NOTE below)
executor: superbot-mineverse seat (next wake)
do: adopt the owner directive below: (a) sim verdict pipeline moves to bigger batches — full content waves per SIM-REQUEST instead of few-item slices; (b) standing mission target: bring all three games to production-grade; (c) precedence — correctness and structural integrity outrank speed; no gate/verdict/golden-parity floor is relaxed.
why: live owner turn in the SuperBot World coordinator session, 2026-07-13 ~21:59Z — batching + production-grade directive for the whole seat.
done-when: the seat's SIM-REQUESTs are filed as full content waves (not few-item slices), the production-grade mission is reflected in seat planning/heartbeat, and no correctness gate has been relaxed in the process.

Owner text, verbatim (quote block, do not paraphrase or fix typos):
> yes make sure the sim works in bigger batches, the goal should be to get all the games to a producition grade level, tho it should not hinder the correct structure, speed is important but not more important than correctness

Provenance: live owner turn in the SuperBot World coordinator session, 2026-07-13 ~21:59Z, relayed by the coordinator dispatch. Context: owner asked why superbot-games fishing has 4 species vs the original's ~21; coordinator offered to batch-pin the remaining roster; owner said yes and generalized. NOTE: inbox.md is normally owner/manager-written; a coordinator relaying a live owner turn is the sanctioned exception (stated here per doctrine).

INTERPRETATION:
(a) sim verdict pipeline moves to bigger batches — full content waves per SIM-REQUEST instead of few-item slices;
(b) standing mission target: bring all three games to production-grade;
(c) precedence: correctness and structural integrity outrank speed — no gate/verdict/golden-parity floor is relaxed.

## ORDER 008 · 2026-07-14T09:35:36Z · status: new

priority: P1
from: fleet-manager (relayed by the Fleet Manager seat per owner directive, coordinator dispatch 2026-07-14; fm PR #193 carries the dispatch log)
executor: next superbot-mineverse session
do:
  (a) FINISH — today (2026-07-14) is the EAP final day. Complete what is completable today from this cited list; anything that can't finish gets parked HONESTLY with a one-line citation of why: nothing unfinished — the three-repo EAP audit merged as PR #107 at 2026-07-14T09:11:39Z (docs/audits/eap-project-audit-2026-07-14.md); (a) reduces to confirming that state holds. Parked (cite): superbot #2058 draft flip + sender-side HMAC (bot-lane), six host env vars (owner), real-endpoint conformance + audit e2e run (env-gated), carried OA-003 (owner click). Premises are from fm recon at 405c8348ed42ac4094d7fa1c261902c738e0e71e — re-verify each live before acting (Q-0120).
  (b) WALKTHROUGH — land docs/eap-closeout-walkthrough-2026-07-14.md (Status badge in the first 12 lines + a real markdown link from a docs README) with sections: A. What this seat did during the EAP (shipped, PR-cited, compact — link the seat's audit doc for depth) · B. Current state + how to run/verify (exact commands) · C. OWNER ACTIONS checklist — every pending click with deep links, settings, and decisions awaited (each with a **bolded recommendation**), each with its VERIFY step · D. a 5-minute verify-it-yourself tour · E. handoff notes (batons, what the next phase needs). Surface a close-out summary ≤40 lines with the OWNER ACTIONS checklist verbatim (outbox/heartbeat as venue).
  NOTE for (b): the walkthrough may link docs/audits/eap-project-audit-2026-07-14.md for depth; OWNER ACTIONS to include: superbot #2058 draft flip + sender-side HMAC, six host env vars, conformance e2e run, carried OA-003.
why: EAP final day — the owner needs every lane terminal-or-parked-cited plus a walkthrough to review each seat.
done-when: every (a) item is terminal or parked-with-citation + the walkthrough doc is on main + the OWNER ACTIONS checklist is surfaced in the lane's close-out report.

## ORDER 009 · 2026-07-15T03:37:08Z · status: new
priority: P2
do: EAP EXTENDED through 2026-07-21 (Anthropic mail, Diana Liu, 2026-07-14T23:07:44Z — 'Claude Code Projects EAP: Extending to Tues 7/21'; metadata reference only). The 2026-07-14 dormancy orders are superseded pending the owner's per-project reboot review — do NOT re-arm routines yet; wait for the owner's per-seat go (the v3.6 reboot prompt IS that go). New features to test during the extension: overview panel, add_repo, Artifact tool (coming), coordinator-comms improvements (coming). fleet-manager and websites are the fleet's source-of-truth homes; see fm docs/pre-reboot-review-2026-07-15.md.
why: the seat's dormancy record predates the extension; without this note a rebooted session would treat dormancy as current
done-when: seat acknowledges on its first rebooted wake
provenance: relayed by the Fleet Manager coordinator on live owner directives, 2026-07-15

## ORDER 010 · 2026-07-16T15:38:36Z · status: new
priority: routine
from: fleet-manager (coordinator dispatch — 2026-07-16 night-audit THIN-lane maintenance rung)
executor: next superbot-mineverse session
do: mirror superbot-idle's PR #142 reconcile-race fix into this repo — the only currently-doable baton item the night audit named for this seat. Read superbot-idle PR #142 (github: menno420/superbot-idle), understand its reconcile-race fix, and port the equivalent fix adapted to this repo's own reconcile path, as one contained tested increment (own PR, land on green). If the fix genuinely does not apply to this repo's architecture, record why in control/status.md and close the ORDER as N/A.
why: the 2026-07-16 night audit read this seat THIN (fresh reboot, green) with its only currently-doable baton item = mirror superbot-idle's #142 reconcile-race fix.
done-when: the reconcile-race fix equivalent to superbot-idle PR #142 is merged on green and control/status.md orders line notes the mirror; OR — if it does not apply — control/status.md records why and the ORDER is closed N/A.
provenance: fleet-manager docs/owner-queue.md item 68 (OQ-THIN-LANE-DISPATCH-2026-07-16) + docs/fleet-triage.md § "2026-07-16 · night audit" @ a5b5359ea937dcc26a7a881a2b59a8ea35eb0ec4; dispatched by the Fleet Manager coordinator and authorized by the owner (menno420) live in the dispatch session, 2026-07-16.
— Fleet Manager
