# superbot-mineverse · status
updated: 2026-07-14T11:34:32Z
phase: HEARTBEAT — ORDER 008 EAP final-day closeout (worker session, coordinator dispatch): FINISH state re-verified at HEAD `c01c013`; owner walkthrough doc landing via branch `claude/eap-closeout-walkthrough` (PR #109: docs/eap-closeout-walkthrough-2026-07-14.md + AGENT_ORIENTATION router link + this heartbeat + outbox close-out summary). No code paths touched.
health: green
kit: v1.15.0
last-shipped: #107 — the seat's three-repo EAP project close-out audit (squash 405c834, committed 2026-07-14T09:11:38Z; docs/audits/eap-project-audit-2026-07-14.md). Latest main commit: c01c013 (#108, manager's ORDER 008 dispatch).
blockers: none
orders: acked=001,002,003,004,005,006,007,008 done=001,002,003,004,005,006,007,008
⚑ needs-owner: the four pending clicks are consolidated in the walkthrough's OWNER ACTIONS checklist (docs/eap-closeout-walkthrough-2026-07-14.md §C, each with a bolded recommendation + VERIFY step): (1) superbot #2058 draft flip + sender-side HMAC — six-field block below (§ OWNER-ACTION, carried); (2) the six host env vars, names only — six-field block: control/outbox.md entry 2026-07-12T21:05Z (outstanding pair: MINING_WRITE_ENDPOINT + MINING_WRITE_SHARED_SECRET; ingest side adds MINING_SNAPSHOT_RELAY_SHARED_SECRET + MINING_SNAPSHOT_PATH web-host-side); (3) real-endpoint conformance e2e once the write pair exists (docs/conformance-runbook.md — env-gated); (4) carried OA-003: pytest as required check on superbot-idle main — six-field block: control/outbox.md entry 2026-07-13T14:56Z (VENUE: hub).
notes: ORDER 008 done= on this line is true as of this PR's merge — the walkthrough doc and this heartbeat land in the same squash (#109), so whenever this line is readable at main HEAD, the doc is on main and the (a) FINISH items are terminal-or-parked-cited. ORDER 008 (a) re-verified live per Q-0120 before acting: #107 squash 405c834 committed 2026-07-14T09:11:38Z, audit doc present at c01c013, heartbeat previously stamped 09:03:48Z, 0 open PRs, control/claims/ README-only. The ≤40-line close-out summary with the OWNER ACTIONS checklist is in control/outbox.md (entry 2026-07-14T11:34Z) per ORDER 008's venue. Ack recorded here, not in the inbox — the inbox is manager-only (one writer per file; gate evidence: outbox entry 2026-07-13, PR #87 run 29290416909).

## ORDER 008 — EAP final-day closeout (this slice)

- (a) FINISH: nothing unfinished — the audit merged as #107 (405c834) and that state holds at c01c013. Parked with citations: superbot #2058 draft flip + sender-side HMAC (bot-lane; seam doc docs/mining-data-contract.md @48e158e) · six host env vars (owner; outbox 2026-07-12T21:05Z) · real-endpoint conformance + audit e2e (env-gated on the write pair) · carried OA-003 (outbox 2026-07-13T14:56Z).
- (b) WALKTHROUGH: docs/eap-closeout-walkthrough-2026-07-14.md — A shipped/PR-cited arc (audit doc linked for depth) · B current state + exact run/verify commands · C OWNER ACTIONS checklist · D 5-minute verify-it-yourself tour · E handoff batons. Badge `owner-guidance` in the first 12 lines; markdown link from docs/AGENT_ORIENTATION.md (docs-gate reachability).
- Tree verified this slice: pip install jsonschema, then python3 -m pytest -q → 610 passed, 1 skipped in 113.59s; bootstrap.py check --strict → only the designed born-red hold for this slice's own card pre-flip (green at flip).

## OWNER-ACTION — sender-side HMAC adoption (superbot #2058 draft flip)

⚑ OWNER-ACTION
WHAT: flip superbot PR #2058 (the bot-side snapshot pusher) out of draft and have the bot lane adopt sender-side HMAC signing so its POSTs authenticate against this repo's live `/api/snapshot/ingest` endpoint.
WHERE: github.com/menno420/superbot → PR #2058 ("Ready for review" button + bot-lane follow-through); host env vars land in the bot host's environment plus the web host per the seam doc `docs/mining-data-contract.md` § Sender (superbot PR #2058).
HOW: sender signs with the repo's ONE canonical scheme (`X-Mineverse-Signature`/`X-Mineverse-Timestamp`, HMAC-SHA256 over `"POST\n/api/snapshot/ingest\n<TIMESTAMP>\n<sha256_hex(BODY)>"`), keyed with `MINING_SNAPSHOT_RELAY_SHARED_SECRET`; env names: `MINING_SNAPSHOT_RELAY_URL` + `MINING_SNAPSHOT_RELAY_GUILD_ID` (bot side), `MINING_SNAPSHOT_RELAY_SHARED_SECRET` + `MINING_SNAPSHOT_PATH` (web host). Values stay owner-side, never in any repo.
RISK: ↩️ reversible — unset the env vars / re-draft the PR to undo; the receive side stays fail-closed (503) whenever the secret or path is unset.
WHY-IT-MATTERS: the FLAG-1 READ relay's receive half is live and tested; live miner data cannot flow until the sender signs and pushes.
UNBLOCKS: live bot→web snapshot flow (FLAG 1), replacing the committed fixture; the staleness badge (VERDICT 056) starts measuring a real feed.
VERIFIED-NEEDED: #2058 is another repo's owner/bot-lane draft and its body names no transport auth (recorded in `docs/mining-data-contract.md` @48e158e); agent sessions hold no write seat on menno420/superbot and no host-env access (docs/CAPABILITIES.md) — receive-side work is complete in this repo (PRs #88/#93), only the sender half remains.

## OPEN PRS

- #109 (`claude/eap-closeout-walkthrough`) — this slice's own landing branch; designed born-red hold until the card flip, enabler-landed after. Nothing else open at stamp time.

## SIBLING LANES

- games/idle lanes: see their own status files/PR trails; the seat-wide EAP record is docs/audits/eap-project-audit-2026-07-14.md.

## ROUTINES (neutral facts)

- Failsafe cron trig_01QctdbvhdcvuSFsCPxdseae bound to the coordinator session; pacemaker chain coordinator-managed.

## NEXT-2 BATON (carried)

1. Serve the games SIM-REQUEST `fishing-full-roster-economy` (29 not-yet-pinned species, filed in games control/outbox.md via games PR #92 squash 21937f3) when the sim verdict returns — first full-content-wave batch under ORDER 007's bigger-batches rule.
2. Verdict-gated waits as before — fishing cook-leg economy SIM-REQUEST (folded by reference into the full-roster batch) + PRESTIGE tuning ruling. Consumer-side snapshot-parity work (3 flavor requireds + slot-map) stays gated on the pending seam ruling (option A) and lands producer-side in product-forge.
