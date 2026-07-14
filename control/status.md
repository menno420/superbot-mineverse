# superbot-mineverse · status
updated: 2026-07-14T09:03:48Z
phase: HEARTBEAT — EAP close-out audit slice (worker session, coordinator dispatch): seat-wide three-repo EAP project audit written and landing via branch `claude/eap-project-audit` (docs/audits/eap-project-audit-2026-07-14.md + router index line + this heartbeat). No code paths touched.
health: green
kit: v1.15.0
last-shipped: #90 — EAP night fleet-cleanup audit doc (another session's parked PR, enabler-landed 2026-07-14T07:20:26Z; squash cb57d02 = main HEAD at this stamp). This seat's own prior slice: #106 improvement-wave close-out heartbeat (0b388f1).
blockers: none
orders: acked=001,002,003,004,005,006,007 done=001,002,003,004,005,006,007
⚑ needs-owner: (1) sender-side HMAC adoption — owner/bot-lane work via the superbot #2058 draft flip; full OWNER-ACTION block below (§ OWNER-ACTION). (2) The six OAuth/write host env vars remain owner-only — six-field block: control/outbox.md entry 2026-07-12T21:05Z (outstanding pair: MINING_WRITE_ENDPOINT + MINING_WRITE_SHARED_SECRET; the ingest side additionally needs MINING_SNAPSHOT_RELAY_SHARED_SECRET + MINING_SNAPSHOT_PATH web-host-side, see §2058 block). (3) Carried: pytest as required check on superbot-idle main (OA-003) — six-field block: control/outbox.md entry 2026-07-13T14:56Z (VENUE: hub).
notes: EAP close-out audit doc lives at docs/audits/eap-project-audit-2026-07-14.md (indexed from docs/AGENT_ORIENTATION.md planted-doc set) — three-repo measured record: scale totals, tooling verdicts, walls, landing/scheduling friction, ceremony ledger, self-fixes, ranked asks, honest gaps. Landing rides the standard born-red card HOLD (claim file control/claims/2026-07-14-eap-project-audit.md, released at card flip; telemetry row in the same PR per Q-0194). Verified at audit start: zero open PRs across all three repos; all three control/claims/ dirs README-only. Tree verified this slice: pip install jsonschema==4.26.0 (requirements-dev.txt) then python3 -m pytest -q → 610 passed, 1 skipped; bootstrap check --strict green apart from the designed in-progress hold on this slice's own card.

## EAP CLOSE-OUT AUDIT 2026-07-14 (this slice)

- Deliverable: docs/audits/eap-project-audit-2026-07-14.md — the seat's definitive EAP audit covering superbot-games, superbot-idle, superbot-mineverse at pinned HEADs (games 1c323c1, idle a23e67c, mineverse cb57d02).
- Headline measured facts (details + citations in the doc): 222 session cards / 525 main commits / 370 PRs opened / 369 merged / 1 closed-unmerged / 0 open across the seat; median time-to-land 4.05 / 0.4 / 1.48 min (games/idle/mineverse); auto-merge-enabler 0 failures observed in the recent windows; every substrate-gate red in the recent windows was a designed born-red hold.
- Prior audit doc (#90, docs/audits/2026-07-13-fleet-cleanup-audit.md) is deltaed, not restated.

## IMPROVEMENT WAVE 2026-07-14 — close-out (owner directive ~01:27Z, relayed by coordinator; 11/11 PRs merged)

- #95 — wave claim (control/claims file; branches `claude/improve-*`).
- #96 — README refresh to HEAD reality (endpoints, stage-d prepared, relay env names, quickstarts).
- #97 — web boot() loading state: "Loading snapshot…" banner until /api/views resolves.
- #98 — staleness-literal drift-guard test: JS `??` fallbacks pinned to views.py constants.
- #99 — 8th achievement "Homesteader" (owns a home structure).
- #100 — sample-vs-live stale-badge UX: `staleness.source` sample|live — demo shows a neutral notice, not a false STALE alarm.
- #101 — minimap co-location: co-located miners grouped into one {x,y,names} point with a ×N badge.
- #102 — server: one shared bounded POST-body reader for action + ingest routes.
- #103 — conformance_run opt-in `--probe-ingest` leg: unsigned 401/503 pass, 200 security-fail.
- #104 — web pixelSVGShell: four hand-rolled SVG shells behind one helper, byte-identical.
- #105 — web sendAction reads Retry-After on 429; rejection line gains "retry in Ns".

Suite 587 → 610 passed + 1 skipped across the wave; `bootstrap.py check --strict` green at every card flip.

Honest drops (considered, not shipped — full reasons in control/outbox.md entry 2026-07-14T03:46Z): 9th hat (hat roster len==8 pinned + modulo reshuffle risk); slot-map promotion (verdict-gated); parity flavor requireds (producer-side — product-forge); CLAUDE.md architecture line (kit-rendered, owner/kit route).

## ORDER 006 — EAP final-night worklist close-out (5/5 shipped; claim #87, close-out heartbeat #94)

1. FLAG-1 snapshot-ingest RECEIVE endpoint — PR #88, squash 82b7caa. `POST /api/snapshot/ingest`, HMAC fail-closed under the ONE canonical `server/actions.py` scheme, v1-validate before persist, atomic replace into `MINING_SNAPSHOT_PATH`; 24 tests.
2. VERDICT 056 applied — PR #89, squash 72536b1. Stale threshold 180 s gains its measured wording across docs/views.
3. Ingest-transport spec addendum — PR #92, squash 48e158e. `docs/mining-data-contract.md` § "Ingest transport & authentication (FLAG-1 seam)" — one written seam for both repos.
4. Snapshot contract constant + field-parity audit — PR #91, squash a73b4ea. `snapshot_contract.py` owns the schema-derived required-field constants; audit at `docs/findings/snapshot-field-parity-audit-2026-07-14.md` — NO producer data debt; misses are 3 consumer-side flavor requireds + a 7/9 gear-slot map.
5. Readiness ingest-route leg — PR #93, squash 0fdb1c5. `scripts/readiness_check.py --probe-ingest`: one deliberately UNSIGNED POST; only 401 `invalid_signature` or 503 fail-closed pass — an unsigned 200 is a SECURITY FAILURE and reds the check; 12 tests.

## ORDER 007 — adoption record (standing seat policy, carried)

- SIM-REQUESTs are filed as full content waves, not few-item slices (no SIM-REQUEST filed from this repo; the rule's live instance is the games-lane fishing-full-roster batch — see NEXT-2 baton).
- Standing mission: all three games to production-grade.
- Precedence: correctness and structural integrity outrank speed — no gate, verdict, or golden-parity floor relaxed (suite 551→587 across the ORDER 006 worklist, 587→610 across the improvement wave).

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

- None at stamp time other than this slice's own landing branch (`claude/eap-project-audit`, PR opened after this stamp — designed born-red hold until the card flip). PR #90 (the 2026-07-13 fleet-cleanup audit) merged 2026-07-14T07:20:26Z as cb57d02.

## SIBLING LANES

- games/idle night runners dispatched by coordinator — see their PR trails.

## ROUTINES (neutral facts)

- Failsafe cron trig_01QctdbvhdcvuSFsCPxdseae bound to the coordinator session; pacemaker chain coordinator-managed.

## NEXT-2 BATON (carried)

1. Serve the games SIM-REQUEST `fishing-full-roster-economy` (29 not-yet-pinned species, filed in games control/outbox.md via games PR #92 squash 21937f3) when the sim verdict returns — first full-content-wave batch under ORDER 007's bigger-batches rule.
2. Verdict-gated waits as before — fishing cook-leg economy SIM-REQUEST (folded by reference into the full-roster batch) + PRESTIGE tuning ruling. Consumer-side snapshot-parity work (3 flavor requireds + slot-map) stays gated on the pending seam ruling (option A) and lands producer-side in product-forge.
