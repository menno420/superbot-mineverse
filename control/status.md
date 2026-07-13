# superbot-mineverse · status
updated: 2026-07-13T23:44:28Z
phase: HEARTBEAT — night-run close-out (control-only fast-lane slice): ORDER 006 EAP worklist complete, all 5 items shipped and squash-merged (#88/#89/#92/#91/#93); ORDER 007 adopted as standing seat policy. Session type: worker, coordinator night dispatch.
health: green
kit: v1.15.0 · check: green
last-shipped: #93 — readiness ingest-route leg (`--probe-ingest`), squash 0fdb1c5 = main HEAD at close; suite 587 passed + 1 skipped.
blockers: none
orders: acked=001,002,003,004,005,006,007 done=001,002,003,004,005,006,007
⚑ needs-owner: (1) sender-side HMAC adoption — owner/bot-lane work via the superbot #2058 draft flip; full OWNER-ACTION block below (§ OWNER-ACTION). (2) The six OAuth/write host env vars remain owner-only — six-field block: control/outbox.md entry 2026-07-12T21:05Z (outstanding pair: MINING_WRITE_ENDPOINT + MINING_WRITE_SHARED_SECRET; the ingest side additionally needs MINING_SNAPSHOT_RELAY_SHARED_SECRET + MINING_SNAPSHOT_PATH web-host-side, see §2058 block). (3) Carried: pytest as required check on superbot-idle main (OA-003) — six-field block: control/outbox.md entry 2026-07-13T14:56Z (VENUE: hub).
notes: ORDER 006 done-when caveat, recorded honestly: its "ack in your inbox thread" clause is machine-unsatisfiable under this repo's own substrate-gate (inbox appends ORDER blocks only; enforcer findings quoted verbatim in control/outbox.md entry 2026-07-13T23:44Z) — the ack lives on this orders: line instead, precedent PR #87; flagged to the manager via the outbox. ORDER 007 marked done on this reading: production-grade mission + full-content-wave SIM-REQUEST rule are recorded as standing seat policy (here + in planning/baton), no correctness gate/verdict/golden-parity floor was relaxed tonight, and no SIM-REQUEST was filed from this repo tonight (none was due — mineverse sim work is verdict-gated waits; the seat's one concrete full-content-wave instance rode the games lane, fishing-full-roster-economy). If the manager reads done-when as requiring a mineverse-filed SIM-REQUEST, treat 007 as still claimed — the policy adoption stands either way. Tree verified this slice: bootstrap check --strict exit 0; python3 -m pytest -q → 587 passed, 1 skipped.

## ORDER 006 — EAP final-night worklist, per-item close-out (all 5 shipped tonight)

1. FLAG-1 snapshot-ingest RECEIVE endpoint — PR #88, squash 82b7caa. `POST /api/snapshot/ingest` (`server/ingest.py` + `server/app.py`), HMAC fail-closed under the ONE canonical `server/actions.py` scheme, v1-validate before persist, atomic replace into `MINING_SNAPSHOT_PATH`; 24 tests.
2. VERDICT 056 applied — PR #89, squash 72536b1. Stale threshold 180 s gains its measured wording across docs/views.
3. Ingest-transport spec addendum — PR #92, squash 48e158e. `docs/mining-data-contract.md` § "Ingest transport & authentication (FLAG-1 seam)": #2058 env names, ~60 s cadence, ingest-auth decision — one written seam for both repos.
4. Snapshot contract constant + field-parity audit — PR #91, squash a73b4ea. `snapshot_contract.py` (repo root, stdlib-only, vendorable) owns the schema-derived required-field constants; audit committed as `docs/findings/snapshot-field-parity-audit-2026-07-14.md` — headline: NO producer data debt; misses are 3 consumer-side flavor requireds (`gear.rarity`, `skills[].xp/xp_max`, `structures[].status`) plus a 7/9 gear-slot map (`tool`/`light` homeless).
5. Readiness ingest-route leg — PR #93, squash 0fdb1c5. `scripts/readiness_check.py --probe-ingest`: one deliberately UNSIGNED POST to the FLAG-1 route; only honest answers are 401 `invalid_signature` or 503 fail-closed — an unsigned 200 is reported as a SECURITY FAILURE and reds the check; 12 tests; suite 587 passed + 1 skipped.

## ORDER 007 — adoption record (standing seat policy)

- SIM-REQUESTs are filed as full content waves, not few-item slices (no SIM-REQUEST was filed from this repo tonight; the rule's live instance is the games-lane fishing-full-roster batch — see NEXT-2 baton).
- Standing mission: all three games to production-grade.
- Precedence: correctness and structural integrity outrank speed — no gate, verdict, or golden-parity floor relaxed tonight (suite grew 551→587 across the worklist).

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

- PR #90 — another session's fleet-cleanup audit, open at base 82b7caa, parked for the auto-merge sweep per its own body. Neutral pointer only; not this lane's work, not touched by this slice.

## SIBLING LANES

- games/idle night runners dispatched by coordinator — see their PR trails.

## ROUTINES (neutral facts)

- Failsafe cron trig_01QctdbvhdcvuSFsCPxdseae bound to the coordinator session; pacemaker chain coordinator-managed.

## NEXT-2 BATON (carried)

1. Serve the games SIM-REQUEST `fishing-full-roster-economy` (29 not-yet-pinned species, filed in games control/outbox.md via games PR #92 squash 21937f3) when the sim verdict returns — first full-content-wave batch under ORDER 007's bigger-batches rule.
2. Verdict-gated waits as before — fishing cook-leg economy SIM-REQUEST (folded by reference into the full-roster batch) + PRESTIGE tuning ruling.
