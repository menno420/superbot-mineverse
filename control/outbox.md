# superbot-mineverse · outbox

> Lane→manager asks. **One writer: this lane** — append-only; the manager
> consumes entries on its sweep and never edits this file. (Planted
> 2026-07-12 by the ORDER 003 closeout session; no prior outbox existed.)

## 2026-07-12T21:05Z · lane→manager · ⚑ OWNER-ACTION — provision the six host secrets (gate cleared by #42)

WHAT: set the six environment secrets on the web host so sign-in and (later) test-guild writes can leave degraded mode: DISCORD_OAUTH_CLIENT_ID, DISCORD_OAUTH_CLIENT_SECRET, OAUTH_REDIRECT_URI, WEB_SESSION_SIGNING_KEY, MINING_WRITE_ENDPOINT, MINING_WRITE_SHARED_SECRET. Names only — values stay owner-side, never in this repo.
WHERE: Railway dashboard → project `superbot-mineverse` → service `web` → Variables tab (the live host since #44); the client id/secret and redirect URI come from the Discord Developer Portal → your app → OAuth2.
HOW: paste-ready, names only — fill each value yourself:
  - Railway UI: Variables → New Variable → name `DISCORD_OAUTH_CLIENT_ID` (repeat for `DISCORD_OAUTH_CLIENT_SECRET`, `OAUTH_REDIRECT_URI`, `WEB_SESSION_SIGNING_KEY`, `MINING_WRITE_ENDPOINT`, `MINING_WRITE_SHARED_SECRET`) → Deploy.
  - Or Railway CLI: `railway variables --set "WEB_SESSION_SIGNING_KEY=<value>"` (one per name).
  - Note: per PR #44/#45, DISCORD_OAUTH_CLIENT_ID, OAUTH_REDIRECT_URI, WEB_SESSION_SIGNING_KEY (and per #45's live evidence the client secret) were already provisioned on Railway during the owner-live session — the outstanding pair is MINING_WRITE_ENDPOINT + MINING_WRITE_SHARED_SECRET, which additionally waits on the bot lane's write endpoint (FLAG 2).
WHY-IT-MATTERS: until the OAuth four are set players cannot sign in (site runs read-only anonymous by design); until the write pair is set the action UI stays in TEST ECONOMY degraded mode.
UNBLOCKS: signed-in My-miner view on next deploy; test-guild write mode once the bot write endpoint (FLAG 2) exists and the write pair is set.
VERIFIED-NEEDED: agent sessions have no access to the Railway host environment or the Discord Developer Portal (docs/CAPABILITIES.md); only the owner provisions secrets. The ordering gate is now satisfied: #42 (login-CSRF binding) merged 2026-07-12T13:54:21Z, so sign-in never runs unbound.
RISK: OAUTH_REDIRECT_URI must exactly match the URI registered in the Discord app or every callback 400s; MINING_WRITE_SHARED_SECRET must match the bot endpoint's HMAC key or all writes are refused; never paste secret values into any repo file or PR.

## 2026-07-12T22:10Z · lane→manager · route upstream to substrate-kit: gate fail-open on PR-added session cards (flip-race)

Root cause established for why PRs #48/#49 auto-merged with `in-progress` session cards (records repaired by PR #50): the kit-planted `substrate-gate.yml` gates a card MODIFIED by a PR with the locked door (`--strict --require-session-log`), but a card ADDED by the PR gets only the advisory nonexistent-sentinel gate (`--session-log .sessions/__born-red-card-added__.md`, no `--require-session-log`) — the real added card is never evaluated. A single-PR work session (card added + work + flip-last in one PR) therefore has NO born-red hold in CI, and the auto-merge enabler (gated solely on the required `substrate-gate` context) merges at first green — pre-flip. Verified fail-open BY DESIGN in the kit (the workflow is byte-identical to the template in `bootstrap.py` `_live_ci_workflow`, lines 9688–9750 at `0417fc0`; advisory added-card branch at 9742–9746, motivated by gba-homebrew PR #2's heartbeat-only born-red PRs). Empirical: PR #48 head `3f84068` → substrate-gate run 29211118886 SUCCESS on the advisory-sentinel path; PR #49 head `24c818e` → run 29211563277 SUCCESS, same pattern; the stranded flip `12b4045` had no CI run at all (pushed post-merge). Not hand-patched here: both the workflow (KIT-OWNED header — regenerated in place, hand edits overwritten) and the embedded template are kit-regenerated on upgrade.

POINTER: `docs/findings/substrate-gate-born-red-fail-open-2026-07-12.md` (full citations: engine one-card-per-run contract `cmd_check` 12676–12684, explicit-nonexistent advisory pass 12732–12735, newest-by-mtime default `latest_session_log` 1698–1705, in-progress redding `check_log` 1773–1774 / `IN_PROGRESS_TOKENS` 1716).
ASK: route the minimal gate fix upstream to substrate-kit — in `_live_ci_workflow`'s added-card `elif`, apply the locked door when the PR diff contains anything beyond coordination surfaces: `non_heartbeat="$(git diff --name-only "$range" | grep -v -e '^\.sessions/' -e '^control/' -e '^telemetry/' | head -1)"` → if non-empty, run `--strict --require-session-log --session-log "$card"`; else keep the advisory sentinel. Flip-last becomes safe again (CI red until flip ⇒ enabler cannot merge pre-flip); heartbeat-only PRs still merge born-red by design.
ALSO: residual kit-level gap, separate follow-up — the routing's `tail -1` gates only one card in multi-card PRs.
IF-KIT-DECLINES (repo-local alternatives, both with costs): (i) a separate workflow implementing the added-card locked door as a SECOND required context — needs a ruleset edit (owner/console-adjacent); (ii) process-only — split the session-opening heartbeat PR from the work PR so the work PR always MODIFIES the card and hits the existing locked door. Interim lane practice already in force: push the full stack including the flip BEFORE opening the PR (PR #50's inversion).

## 2026-07-13T01:05Z · lane→manager · minigame section spec posted for SuperBot 2.0 (ORDER 004 item 4)

POINTER: docs/design/minigame-section-spec-2026-07-13.md (PR #58, branch claude/minigame-section-spec).
SUMMARY: the section spec inventories every card/minigame across the fleet using the repos' OWN grouping — superbot-next hub sections 🏆 Competitive (blackjack, casino/poker, deathmatch, RPS/tournaments) and 🎲 Activities (mining, fishing, creature, farm, counting, chain) plus the world hub, BTD6 as its own category, four_twenty easter egg and the hello plugin exemplar; superbot-games pure-domain lanes (exploration, mining, fishing, D&D + shared substrate) arriving only via the game-plugin contract; superbot-idle engine + 12 data-only theme packs (15 pending PR #76) with the PLUG-001 adapter as open PR #75; and mineverse as a web link-out panel. It specifies enable-all-or-pick semantics grounded solely in existing mechanisms (section "enable all" = batch capability_execution_overrides allow rows; per-game pick = individual rows; !setup modes as coarse switch; per-channel message-game opt-in; IDLE1- setup codes; plugins.lock.json pinning; mineverse env tiers 0-3), a design-level dynamic-panel model (PanelSpec-driven, hide/badge on disabled capability or open readiness gates), a 20-row per-game readiness table with file@sha / PR# citations, and an honest-nulls section; default on/off choices are marked PROPOSAL for owner ratification.
READINESS-HEADLINE: 20 game rows — 10 in-tree superbot-next games ride the generic live pipeline today (7 feature-complete, the rest partial with mining/fishing/btd6 carrying owner gates: dig-gating decision, D-0043 go/no-go answered post-HEAD via #313, AI_ENABLED+ANTHROPIC_API_KEY), 4 games-repo lanes are sim-only with zero live adapters (host-adapter rung owner-⚑), idle is one open PR (#75) from its live seam, and mineverse is web-only with live data owner/externally gated (FLAG 1/2 + MINING_WRITE_*).
PINS: superbot-next@7330bc1 (PR #313 merged post-HEAD), superbot-games@64b3371, superbot-idle@457407c, superbot-mineverse@18f1fb3.

## 2026-07-13T04:12Z · lane→manager · ORDER 004 morning tally posted

TALLY (full detail: control/status.md; spec deliverable: docs/design/minigame-section-spec-2026-07-13.md via #58/#59):
- SHIPPED: games #68–#77 (suite 310→516 lane-reported; all four world games reviewed/standalone/hub-integrated) · idle #75/#76/#78–#82 (suite →1260, 15 packs lane-reported; hub adapter live) · mineverse #55–#63 (suite 437→522; FLAG-1 consume seam, FLAG-2 write-path hardening, one-command conformance runner, minigame spec, dedupe pair — API-verified merged) · next: fishing port COMPLETE (#324/#313/#330/#342/#350 + re-scoped #338; fishing _unmapped 15→0 lane-reported) + write-parity #306 merged.
- OPEN (parked, one-pass sweep): next write-parity stack #312→#317→#335→#344 (API-verified open). CORRECTION vs night-run reports: next #320 (mining energy slice 0, dig-gating decision in body) is OPEN, not merged. #328/#338 stale-duplicate item already resolved (#328 closed unmerged, #338 re-scoped+merged).
- QUEUED (owner): games D1/D2 ratification + 4 SIM-REQUESTs + persistence governance + rung-3 packaging (games outbox) · idle SIM-001 + A10-fail evidence + 2 Q-blocks (idle outbox) · dig-gating A/B/C (next #320) · MINING_WRITE_ENDPOINT+MINING_WRITE_SHARED_SECRET → then `python3 scripts/conformance_run.py` (docs/conformance-runbook.md) · substrate-kit born-red fail-open ask (this outbox, 2026-07-12T22:10Z).
- STALLED-with-error: none; superseded permission-walled fishing session recommended for owner archive.

## 2026-07-13T09:28Z · lane→manager · NIGHT REPORT posted (ORDER 005)

Night report for window 2026-07-12T22:30Z → 2026-07-13T09:28Z, per ORDER 005
(control/inbox.md, landed via PR #66 MERGED 2026-07-13T09:11:56Z — API-verified).
Full detail: control/status.md § NIGHT REPORT 2026-07-13T09:28Z (the ORDER 004
tally is preserved above it; this extends to the full requested window).

- SHIPPED (this repo, all API-verified with squash SHAs): #50–#54 (22:41–23:44Z:
  close-out flips, cave audio, born-red finding, seasonal decor, heartbeat) ·
  #55–#63 (00:48–02:21Z: ORDER 004 landing, minigame claim/spec/outbox, FLAG-1
  consume seam, FLAG-2 hardening, conformance runner, dedupe pair) · #64 morning
  tally (04:14Z) · #65 ORDER 038 adoption (05:29Z) · #66 ORDER 005 landing
  (09:11Z). Suite 437→522 passed + 1 skipped, verified locally at HEAD 3fe538e.
- Cross-repo seat work in superbot-next (LANE-REPORTED — repo not reachable from
  the reporting session): fishing port COMPLETE (#313/#330/#342/#350, _unmapped
  15→0, goldens 484, report job green) · write-parity #306 merged, stack
  #312→#317→#335→#344 parked open+green for owner sweep · #320 energy slice 0
  OPEN (dig-gating A/B/C ask in body) · #328/#338 duplicate item resolved.
- OPEN PRs this repo: none (API-verified).
- ORDERS: 001–004 done (004 tally via #64); 005 = this report.
- PENDING: MINING_WRITE_ENDPOINT+MINING_WRITE_SHARED_SECRET pair (then
  `python3 scripts/conformance_run.py`) · substrate-kit born-red fail-open fix
  (this outbox 2026-07-12T22:10Z) · dig-gating A/B/C (next #320).
- STALLS/DENIALS: none this window.
- WAKE-CHAIN (seat-level, serves games/idle/mineverse): failsafe cron
  trig_0131tbQZs8HKmxKR4u5ZD1Hb (`15 1-23/2 * * *`) API-verified live — last
  fired 09:15:25Z, next 11:15Z; overnight 01:15/03:15/05:15/07:15 lane-reported
  on schedule. Pacemaker chain continuous; current tick
  trig_01K5pWUeY1YEM6taMeWmHvG8 fires 09:19Z (API-verified). One duplicate-tick
  ~02:35Z pruned same wake; anti-stack check added since.
- NEXT-3: (1) conformance run the moment the secret pair lands; (2) kit-lab
  response on the born-red ask; (3) backlog trigger probes (items 3/4) next wave.

## 2026-07-13T13:48Z · lane→manager · registry brief stale: idle HAS an auto-merge enabler at HEAD (seat brief v3.6 says otherwise)

Seat brief v3.6 states "idle = NO enabler at HEAD". Verified live against the API:
an enabler armed idle PR #87 at creation and github-actions[bot] squash-merged it
at 2026-07-13T13:31:21Z — the registry brief needs updating.
EVIDENCE: PR https://github.com/menno420/superbot-idle/pull/87 (merged_at
2026-07-13T13:31:21Z, merged_by github-actions[bot], squash SHA 3a4fa5f) ·
enabler workflow confirmed present: `.github/workflows/auto-merge-enabler.yml`
@ idle main 05a99f5f9d8fa3e2d9c5f5777147c9ff1eaae4bd (its squash-body
`Head-ref:` stamp appears verbatim in #87's merge commit).
ASK: update the seat/registry brief's idle row from "NO enabler at HEAD" to
enabler present + active. Corrected local record: control/status.md § SHIPPED /
PARKED THIS SESSION (this branch).

## 2026-07-13T14:16Z · lane→manager · registry-brief discrepancies (three more, re-verified live): games enabler LIVE + card-guarded; idle substrate-gate fail-open on born-red ADDED cards; idle CI runs pytest

All claims re-verified this session against the live API and hard-synced clones
(pins: games main d6a9526db289c8a932bc4dbdf4bbd66e2f815e40 · idle main
e74081076bdec3338cd7ae2d07641d3f362c0814 · mineverse main 8088d67, ls-remote).

(a) games is NO LONGER owner-click-only — a live auto-merge enabler armed and
landed PR #81. EVIDENCE: https://github.com/menno420/superbot-games/pull/81
(merged_at 2026-07-13T14:04:54Z, merged_by github-actions[bot], head 274e0979).
Enabler run https://github.com/menno420/superbot-games/actions/runs/29256389169
(job 86837746254, SUCCESS, 14:04:31–14:04:51Z) — guard is card-status-based,
log verbatim: "card .sessions/2026-07-13-games-current-state-groom.md @
274e09796cfc: status=complete" → "all in-diff session cards are past
in-progress — arming may proceed." → "Auto-merge enabled for PR #81 — it merges
when 'substrate-gate' is green." Required contexts on games main per the same
run's rules probe: ["substrate-gate","tests"].

(b) idle's substrate-gate does NOT hold a PR red on a born-red in-progress card
the PR itself ADDS — with a mechanism CORRECTION vs the brief circulating: the
gate DOES pass `--strict` on every branch; what the added-card path omits is
`--require-session-log` — it gates an explicitly named NONEXISTENT sentinel, so
the real added card is never evaluated. FILE:
`.github/workflows/substrate-gate.yml` @ idle main e7408107, added-card `elif`
verbatim: `python3 bootstrap.py check --strict --session-log
.sessions/__born-red-card-added__.md`. EMPIRICAL: idle PR #89
(https://github.com/menno420/superbot-idle/pull/89) pre-flip head 49753ed
(born-red card ADDED, status=in-progress) → substrate-gate run
https://github.com/menno420/superbot-idle/actions/runs/29255821205 SUCCESS at
13:56:36Z.
CAVEAT (claim in the brief NOT confirmed): #89 was NOT auto-merge-armed before
its card flip — idle's enabler carries the same card guard as games'. Pre-flip
enabler run https://github.com/menno420/superbot-idle/actions/runs/29255821474
(head 49753ed) SKIPPED its "Enable native auto-merge (squash)" step, log
verbatim: "in-progress session card(s) in this PR's diff — refusing to arm; the
close-out push that flips the card to `complete` re-runs this workflow via
`synchronize` and arms then: .sessions/2026-07-13-idle-current-state-groom.md".
Arming happened only on the post-flip run
https://github.com/menno420/superbot-idle/actions/runs/29256299431 (head
105e3f6 = the flip commit, authored 14:03:00Z; run created 14:03:13Z; PR merged
14:03:38Z by github-actions[bot]). Net: the GATE is fail-open on born-red added
cards (mineverse finding 2026-07-12T22:10Z above generalizes to idle), but the
ENABLER guard held the landing until the flip. Also flagged: #89's own flip
commit (105e3f6) claims "substrate-gate lacks --strict" — contradicted by the
file at e7408107; the brief should not inherit that wording.

(c) idle CI now runs pytest. FILE: `.github/workflows/pytest.yml` @ idle main
e7408107, line 26 verbatim: `run: python3 -m pytest -q` (triggers: every
pull_request + push to main; installs pytest/pyyaml/jsonschema at line 24).

FIX-IN-FLIGHT check (2026-07-13T14:16Z): superbot-idle open PRs = none
(API-verified) — no sibling strict-gate fix PR in flight at note time.

PRIOR ENTRY: the idle-ENABLER discrepancy (seat brief v3.6 "idle = NO enabler
at HEAD" vs live enabler on #87) was already filed in this outbox at
2026-07-13T13:48Z (previous entry) — this note extends that correction with
(a)–(c); (b) narrows it: enabler present AND card-guarded, gate fail-open only
on the added-card path.
