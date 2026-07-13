# Coordinator session retro — 2026-07-13 (boot 2026-07-12T20:39Z → ender 2026-07-13T~12:00Z)

> **Status:** `historical` — seat retro, written at session close by the
> close-out worker from the coordinator's wrap-up brief. Retro close-out
> state per the ender protocol: **Status:** `complete`. Merged work and
> live source control always win over this narrative; merge states were
> verified where reachable (mineverse via API; games/idle against each
> repo's main; superbot-next lane-reported — that repo is outside this
> reporting session's scope). Companion records: the session card
> (`.sessions/2026-07-13-coordinator-ender.md`), the heartbeat
> (`control/status.md`), and the ORDER 004/005 report sections preserved
> in this repo's git history (`control/status.md` @ `e44a80c` and earlier).

The seat ran one continuous session, ~15.5 hours, covering the SuperBot
World trio (superbot-games / superbot-idle / superbot-mineverse) plus
cross-repo seat work in superbot-next.

## (a) Shipped & parked

**Shipped (coordinator seat, one session):**

- **Boot + trigger cutover** — old failsafe `trig_01KQbKNiSVfZRWutKEWFx2q2`
  deleted, new failsafe `trig_0131tbQZs8HKmxKR4u5ZD1Hb` armed
  (`15 1-23/2 * * *`).
- **ORDER 004 night run — all 5 items delivered.** ~35 merged PRs across
  the seat: superbot-games #65–#77 (all four world games
  reviewed/standalone/hub-integrated, suite 310→516), superbot-idle
  #74–#86 (15 packs, adapter live, suite →1260), superbot-mineverse
  #46–#73 (FLAG-1 consume seam, FLAG-2 write-path hardening, one-command
  conformance runner, dedupe waves; suite 437→551), superbot-next fishing
  port #313/#330/#342/#350 + the write-parity lane.
- **Minigame section spec** for SuperBot 2.0 (mineverse #58 landing, #59
  outbox pointer; `docs/design/minigame-section-spec-2026-07-13.md`).
- **Morning tally** (ORDER 004 done-when, mineverse #64).
- **Night reports per fm orders** — games #79, idle #84, mineverse #67
  (ORDER 005).
- **Day wave:** two-plugin headless proof (superbot-next #370),
  compile-time command/group collision gate now in required CI (#377),
  idle live-path fixes (#85/#86 — three real bugs fixed at source),
  fishing cast-depth #373 (6 codex findings fixed with regression tests,
  1 refuted with oracle citation), mineverse lane waves to suite 551.
- **fm ORDER 037 stamp fix** (games #76) and **ORDER 038 adoption**
  (mineverse #65 — reviewer-reply authenticity gate).

**Parked for the owner:**

- superbot-next write-parity stack **#312 → #317 → #335 → #344 → #371**
  (owner-click; stack order in the PR bodies).
- Render-dispatch seam (held on the owner's a/b letter) · dig-gating
  A/B/C energy decision (superbot-next #320 body) · D2 audit-schema
  ratification · SIM-REQUESTs ×5 · persistence governance + rung-3
  packaging decisions (games outbox) · `MINING_WRITE_ENDPOINT` +
  `MINING_WRITE_SHARED_SECRET` secret pair (this repo's outbox,
  2026-07-12T21:05Z) · substrate-kit born-red fix ask
  (`control/outbox.md` 2026-07-12T22:10Z, landed via PR #52).

## (b) Struggles

1. **Permission-walled fishing session.** A sibling session held a
   complete superbot-next fishing port container-local; the permission
   layer denied pushing it out even after an owner chat grant — the wall
   is settings-level (session repo-scope is fixed at creation), so the
   grant could not clear it. Resolved by dispatching a fresh,
   correctly-scoped rebuild lane (#330/#342/#350). **Lesson: session
   repo-scope is set at creation — rebuild beats unblocking.** (The same
   wall class reproduces trivially: a GitHub MCP call against
   superbot-next from this seat's worker answers `Access denied:
   repository "menno420/superbot-next" is not configured for this
   session. Allowed repositories: …`.)
2. **Pacemaker double-tick ~02:35Z.** Two send_laters stacked when a
   scheduled wake raced an event-triggered turn; pruned the same wake. An
   anti-stack pre-check (list before arm) was added to every subsequent
   arming — no recurrence in ~20 arms.
3. **Workers ending on armed timers.** Two workers ended their turn on
   armed CI-wait timers and never resumed (known platform class:
   send_later does not resume background workers). Harmless both times —
   the enabler finished the merges — but every subsequent worker brief
   added "poll inline, never end on a timer".
4. **Born-red gate FAIL-OPEN for PR-ADDED cards.** The kit's session gate
   proved advisory for cards ADDED by a PR (root cause: bootstrap's
   advisory sentinel path), stranding the #48/#49 flips. Interim practice
   adopted: push the full stack including the flip BEFORE opening the PR.
   Kit fix ask routed upstream via the outbox (PR #52; finding at
   `docs/findings/substrate-gate-born-red-fail-open-2026-07-12.md`).
5. **GitHub silently skips ALL pull_request CI on born-conflicted PRs** —
   it looks exactly like swallowed webhook events. Hit twice on
   append-magnet files (control ledgers). Fix: merge main in and
   union-resolve; checks attach immediately.

## (c) Went well

- **Worker-relay for every mechanic.** This venue's coordinator seat has
  no direct shell/git/trigger tools; ~40 workers executed every
  operation with zero laundering incidents.
- **Lane autonomy with park-green discipline** plus "say the word / stand
  down" honesty — Q-0089 held: three lanes declared themselves dry rather
  than inventing filler work.
- **ORDER 038 authenticity gate applied same-day** to a real codex round:
  3/3 replies authentic, 1 refuted-with-citation on #373.
- **Decide-and-flag kept the night run moving** through D1/D2 and
  namespace choices, with every default documented reversible.
- **The oracle-faithfulness bar caught real money bugs:** the coral
  double-spend, the pot preset, and the tournament payout stranding.

## (d) Surprises & open questions

- **Enablers appeared mid-night in games/idle (owner-installed),**
  flipping landing paths from park-green to land-on-green; the "no
  enabler in idle / self-arm retired" seat notes went stale within hours.
  Successor: **re-verify landing paths at boot — do not trust the brief.**
- Open: the kit-lab response to the born-red ask; the
  fresh-session-per-fire cron delivery question (0-for-2 fleet-wide)
  untouched this session; the energy dig-gating letter still pending.

## (e) One line

Lessons baked = kit gate fix ask (outbox, PR #52, routed upstream),
collision gate now in required CI (superbot-next #377), anti-stack +
no-timer rules encoded in this retro and in the heartbeat baton for the
successor's worker briefs.
