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

## 2026-07-13T14:56Z · lane→manager · ⚑ OWNER-ACTION — make `pytest` a required check on superbot-idle main (GREEN≠TESTED) + idle kit v1.15.0 upgrade report

⚑ OWNER-ACTION · VENUE: hub
WHAT: add the `pytest` check as a required status context on menno420/superbot-idle's
main branch protection/ruleset, alongside the two currently required
(`substrate-gate`, `theme-gate`).
WHERE: GitHub → superbot-idle → Settings → Branches (or Settings → Rules → Rulesets)
→ the `main` protection rule → "Require status checks to pass before merging".
HOW: click path — in that rule's status-check search box type `pytest`, select it,
Save changes. Or paste-ready CLI (classic branch protection):
`gh api -X PATCH repos/menno420/superbot-idle/branches/main/protection/required_status_checks -f "contexts[]=substrate-gate" -f "contexts[]=theme-gate" -f "contexts[]=pytest"`
(if main is governed by a ruleset instead, add `pytest` to the ruleset's required
status checks in the UI — same three contexts, click only).
WHY-IT-MATTERS: GREEN≠TESTED on idle — the pytest suite runs in CI on every PR and
push (superbot-idle `.github/workflows/pytest.yml` @ e740810, line 26 verbatim:
`run: python3 -m pytest -q`; re-verified byte-identical at current main 96cd635) but
its check is NOT required (idle enabler run 29255821474 rules probe, log verbatim:
`required contexts (2): ["substrate-gate","theme-gate"]`), so a PR can merge with the
test suite red or still running — nothing server-side blocks it.
UNBLOCKS: server-side GREEN=TESTED for every idle merge; retires the manual "run
pytest before merge" doctrine line and the enabler's not-required warning text (idle
PR #91's truth-fix commit e703fd3 had to document pytest as not-required).
VERIFY: the next idle PR lists `pytest` among its required checks; the enabler log's
rules probe reports 3 required contexts.
VERIFIED-NEEDED: branch-protection/ruleset settings are owner-console-only — agent
sessions hold no admin scope on fleet repos (same wall class as the ruleset-edit
alternative already parked in this outbox 2026-07-12T22:10Z, IF-KIT-DECLINES (i):
"needs a ruleset edit (owner/console-adjacent)"). Live probe of the current state:
enabler run 29255821474 read the protection rules and reported only the 2 contexts
quoted above.
RISK: ✅ reversible — a settings toggle; remove the `pytest` context the same way if
it ever needs to come out.
**Recommend: Y — add it.** Reply Y/N.

KIT-UPGRADE OUTCOME REPORT (idle, same slice — facts, cited):
- idle kit upgraded v1.7.1 → v1.15.0 via superbot-idle PR #91, squash-merged as
  96cd635 by the repo enabler (merged_by github-actions[bot] 2026-07-13T14:48:42Z,
  API-verified; 96cd635 = idle main HEAD by ls-remote at 14:55Z). The new
  `--added-card` born-red HOLD fired live: designed-red substrate-gate run
  29259353167 on pre-flip head e703fd3; green post-flip run 29259492736. pytest at
  merge: 1260 passed, 1 skipped.
- Fleet note: v1.7.1-class gates elsewhere still carry the broken ADDED-card path
  (advisory absent-sentinel only — this outbox 2026-07-12T22:10Z): idle #89 head
  49753ed went gate-green pre-flip (run 29255821205).
- Kit bug worth routing to kit-lab via the manager: kit v1.15.0's upgrade detects a
  host-added enabler customization as a carve-out, banks it, then regenerates over
  it anyway — both live adopters hand-reverted to their host enablers (games @
  d6a9526; idle #91 restored the #77/#90 enabler byte-equal). Proposal:
  keep-host-on-structural-carve-out.
- Idle lane-owed follow-up: idle control/status.md `kit:` line still says v1.7.1 —
  bump to v1.15.0 on that lane's next heartbeat overwrite.

## 2026-07-13T15:08Z · lane→manager · registry-brief drift: mineverse CI checks are substrate-gate + pytest — no `schema-gate` check context exists

The registry seat brief for mineverse states CI = "substrate-gate + schema-gate".
Live observation 2026-07-13T15:08Z, verified at main bf9ee98 and via the GitHub API:

- Workflows at HEAD bf9ee98 (`.github/workflows/`): `substrate-gate.yml`
  (workflow + job `substrate-gate`), `schema-gate.yml` (workflow NAMED
  `schema-gate`, but its single job — hence its check CONTEXT — is `pytest`;
  it runs `python3 -m pytest -q`, file line 22), `auto-merge-enabler.yml`
  (workflow `auto-merge-enabler`, job `enable-auto-merge`).
- Check contexts observed on merged PR #77 (head 9db52dd): `substrate-gate`
  (run 29257580397), `pytest` (run 29257577192), `enable-auto-merge`
  (run 29257577294) — all SUCCESS.
- Check contexts observed on merged PR #78 (head 68815c9): `substrate-gate`
  (run 29260138542), `pytest` (run 29260140384), `enable-auto-merge`
  (run 29260140367) — all SUCCESS.
- Required contexts on main, server-side: the enabler's rules probe on run
  29260140367 (job 86850885591), log verbatim:
  `required contexts (2): ["substrate-gate","pytest"]`.
- No check context named `schema-gate` appears on either PR or in the rules
  probe. The repo's own ledger already records this correctly:
  docs/current-state.md ("both `substrate-gate` AND `pytest` (the schema-gate
  workflow's job) are required status checks on main").

ASK: correct the registry seat brief for mineverse to CI = `substrate-gate` +
`pytest` (both required on main), noting `schema-gate` is only the workflow
display name wrapping the pytest job, never a check context.

## 2026-07-13T16:15Z · lane→manager · route to kit-lab: kit upgrade report omits pre/post sha256 pairs for kit-owned CI files — customization loss is only auditable via a manual byte-copy ritual

The kit's upgrade carve-out scan prints only `ran, 0 found` plus a `kept`/
`regenerated` verdict per kit-owned CI file — it never records the pre/post
sha256 pair. "kept (already current)" on a clean wave and "regenerated and
STRIPPED the hand-installed guards" on a dirty one are therefore
distinguishable only if the operator did a manual byte-copy before running the
tool, then byte-compared after.

AFFECTED WAVES (both live, cited):
- mineverse PR #80 (kit v1.8.0 → v1.15.0, merged 2026-07-13T16:05:32Z as
  1520e05): proving `auto-merge-enabler.yml` survived required a pre-upgrade
  byte-copy + post-upgrade `cmp`/sha256 compare (sha256 `64f9db41…c64c84` both
  sides — evidence lives only in the PR body/card, not in
  `.substrate/upgrade-report.md`).
- superbot-idle PR #91 (kit v1.7.1 → v1.15.0, squash 96cd635): the regen DID
  strip that repo's hand-installed enabler guards and the loss was caught by
  the same manual ritual, then hand-reverted (also filed in this outbox
  2026-07-13T14:56Z, kit-upgrade outcome report).

ASK: route to kit-lab via the manager — have the kit's upgrade report log
`<file>: pre=<sha256> post=<sha256> (kept|regenerated)` for every kit-owned
workflow the carve-out scan considers, so customization loss is mechanically
auditable from `.substrate/upgrade-report.md` alone, no operator ritual
required. Origin: mineverse `.sessions/2026-07-13-kit-upgrade-v1150.md`
§ Session idea (dedup-checked there against the games and idle wave ideas).

## 2026-07-13T23:44Z · lane→manager · ORDER 006's done-when "ack in your inbox thread" is machine-unsatisfiable under this repo's own substrate-gate — fix the ORDER grammar or the gate

ORDER 006 (control/inbox.md) closes with `done-when: work the list top-down
across tonight's wakes; ack in your inbox thread; heartbeat progress per
item.` — but no lane can write an ack into `control/inbox.md`: the
substrate-gate's inbox enforcer rejects BOTH available shapes, findings
quoted verbatim from the kit engine (`check_inbox_append` /
`_order_grammar_findings`, verified live on PR #87 run 29290416909):

- any edit to existing bytes (e.g. an ack line under the ORDER):
  `[inbox-not-append] control/inbox.md changed non-append vs the merge-base
  — the one-writer/append-only law (control/README.md) allows only
  additions at the end; an existing ORDER was edited, reordered, or
  deleted. Restore the prior bytes verbatim and append your new ORDER block
  instead.`
- any non-ORDER append (e.g. an ack block at the end):
  [inbox-order-grammar] "appended content that is neither the file header
  nor a `## ORDER` block — the inbox appends ORDER blocks only
  (control/README.md order format)."

This is the protocol working as designed (one writer: the manager), so the
ack was recorded on the status.md `orders:` line instead — precedent PR #87
(the 006+007 claim), close-out on this slice's heartbeat.

ASK: fix one side so the next ORDER's done-when is satisfiable as written —
either (a) the ORDER grammar/template stops asking for inbox-thread acks
(done-when points at the status `orders:` line, where acks already live),
or (b) the gate grows a sanctioned ack shape (e.g. an `ack:` append form).
Recommend (a): zero code, matches the one-writer law.

NIGHT SUMMARY (one line): 6/6 PRs merged tonight incl. the claim
(#87 claim · #88 ingest endpoint · #89 VERDICT 056 · #92 transport addendum
· #91 contract+parity audit · #93 readiness probe); suite 551→587.

## 2026-07-14T03:46Z · lane→manager · improvement wave 2026-07-14 complete — 11/11 PRs merged, suite 587→610

Owner directive (relayed by coordinator, 2026-07-14 ~01:27Z): "see if there
is anything else you can come up with or improve".

DONE: 11/11 wave PRs merged to main — #95 wave claim · #96 README refresh ·
#97 boot loading state · #98 staleness drift-guard test · #99 8th
achievement "Homesteader" · #100 sample-vs-live stale-badge UX
(staleness.source) · #101 minimap co-location ×N badge · #102 shared
bounded-body reader · #103 conformance --probe-ingest leg · #104
pixelSVGShell dedupe · #105 Retry-After 429 UI. Suite 587 → 610 passed +
1 skipped; bootstrap check --strict green at every card flip. Wave claim
file deleted at session close per control/claims/README.md.

HONEST DROPS (considered, not shipped — each with its reason):
- 9th hat: the hat roster's len==8 is pinned by tests and feeds a modulo
  reshuffle — growing it silently reshuffles every miner's existing hat, a
  player-visible identity change needing an owner/verdict call, not a wave
  slice.
- Gear slot-map promotion (`tool`/`light` homeless, 7/9 map): verdict-gated
  — the slot taxonomy is a contract surface, not a unilateral lane edit.
- Snapshot-parity flavor requireds (`gear.rarity`, `skills[].xp/xp_max`,
  `structures[].status`): producer-side data work that belongs in
  product-forge, not in this consumer repo.
- CLAUDE.md architecture line (stale vs the live write/ingest paths): the
  file is kit-rendered from interview slots — the fix routes owner/kit
  (re-render), a hand edit would be overwritten.

NOTE: consumer-side snapshot-parity work remains gated on the pending seam
ruling (option A) plus the producer-side half in product-forge; nothing
further is actionable in this repo until that ruling returns.
