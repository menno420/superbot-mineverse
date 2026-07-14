# EAP close-out walkthrough — SuperBot World seat @ mineverse (2026-07-14)

> **Status:** `owner-guidance`
>
> The owner's review-it-yourself walkthrough for this seat at EAP close
> (ORDER 008, `control/inbox.md` @ `c01c013`, landed via PR #108). Written
> 2026-07-14T11:25Z against main `c01c013`. Depth lives in the seat's merged
> EAP audit — [EAP project close-out audit
> (2026-07-14)](audits/eap-project-audit-2026-07-14.md) (PR #107, squash
> `405c834`, merged 2026-07-14T09:11:38Z) — this doc restates nothing it can
> link. Every pending owner click is in §C with a VERIFY step.

## A. What this seat did during the EAP (compact, PR-cited)

Seat-wide (superbot-games · superbot-idle · superbot-mineverse), measured in
the audit doc §1: **370 PRs opened / 369 merged / 1 closed-unmerged / 0 open**,
525 main commits, 222 session cards, window 2026-07-09 → 2026-07-14. For the
full record (walls ledger, landing friction medians, ceremony costs, ranked
asks) read the linked audit — the compact mineverse arc:

- **Stage 0–a — read path:** walking skeleton (sample snapshot → stdlib
  server → static frontend, PR #2); versioned read contract
  (`docs/mining-data-contract.md`); Discord OAuth sign-in (stage b) with
  login-CSRF binding hardened in PR #42 (merged 2026-07-12T13:54:21Z).
- **Stage c — write path:** write contract v1 (PR #13), HMAC-signed
  `POST /api/action` relay + test-economy UI, shim executor + one-command
  conformance runner (`scripts/conformance_run.py`, runbook
  `docs/conformance-runbook.md`).
- **FLAG-1 receive side:** `POST /api/snapshot/ingest` — HMAC fail-closed,
  v1-validated, atomic persist (PR #88); stale-indicator T=180s per VERDICT
  056 (PR #89); ingest-transport seam addendum (PR #92); schema-derived
  snapshot contract constants + field-parity audit (PR #91); readiness
  ingest probe leg (PR #93).
- **Improvement wave 2026-07-14** (11/11 merged, PRs #95–#105): README
  refresh, boot loading state, drift-guard test, 8th achievement,
  sample-vs-live staleness UX, minimap co-location, shared body reader,
  conformance ingest leg, SVG shell dedupe, Retry-After UI.
- **Close-out records:** fleet-cleanup audit (PR #90) and the seat's EAP
  project audit (PR #107). Test suite grew 437 → **610 passed + 1 skipped**
  across the final window.

## B. Current state + how to run / verify

State at main `c01c013`: stages 0–c **done**, stage d **prepared** (cutover
checklist `docs/live-prod-cutover.md`); reads are degraded-by-default (the
committed sample serves until `MINING_SNAPSHOT_PATH` + a signing sender
exist); writes are TEST-ECONOMY only and honestly 503 until the owner env
vars land (§C). No secrets anywhere in the repo — by design.

Exact commands (no secrets, no network needed):

```
git clone https://github.com/menno420/superbot-mineverse && cd superbot-mineverse
pip install jsonschema                # the one test dep (requirements-dev.txt)
python3 -m pytest -q                  # expect: 610 passed, 1 skipped
python3 bootstrap.py check --strict   # substrate/docs/heartbeat gates, exit 0
python3 server/app.py                 # http://127.0.0.1:8000 (PORT overrides)
```

Operational checks for a configured host (print env-var NAMES and SET/UNSET
only — never a value):

```
python3 scripts/readiness_check.py --probe-ingest   # cutover readiness + one unsigned ingest probe (401/503 pass; 200 = security failure)
python3 scripts/conformance_run.py --probe-ingest   # WRITE-contract conformance sweep against the real executor
```

## C. OWNER ACTIONS checklist

Every pending click, each with a **bolded recommendation** and a VERIFY step.
Env-var **names only** — values stay owner-side, never in any repo.

1. **Flip superbot PR #2058 out of draft and have the bot lane adopt
   sender-side HMAC signing** (the FLAG-1 sender half; the receive half is
   live and tested here via PRs #88/#93).
   - WHERE: <https://github.com/menno420/superbot/pull/2058> → "Ready for
     review", then the bot lane implements signing per
     `docs/mining-data-contract.md` § "Ingest transport & authentication"
     (PR #92).
   - RISK: ↩️ reversible — re-draft the PR / unset the env vars; the receive
     side stays fail-closed (503) whenever secret or path is unset.
   - VERIFY: after the bot deploys, the site's staleness badge reads a live
     feed (`staleness.source: live`, PR #100) instead of the sample notice;
     `python3 scripts/readiness_check.py --probe-ingest` on the host passes.
2. **Provision the six host env vars on Railway** (names only):
   `DISCORD_OAUTH_CLIENT_ID`, `DISCORD_OAUTH_CLIENT_SECRET`,
   `OAUTH_REDIRECT_URI`, `WEB_SESSION_SIGNING_KEY` (the OAuth four —
   evidence in PRs #44/#45 says these were already set during the owner-live
   session), plus the outstanding write pair `MINING_WRITE_ENDPOINT` +
   `MINING_WRITE_SHARED_SECRET`; the ingest side additionally needs
   `MINING_SNAPSHOT_RELAY_SHARED_SECRET` + `MINING_SNAPSHOT_PATH` (web host)
   and `MINING_SNAPSHOT_RELAY_URL` + `MINING_SNAPSHOT_RELAY_GUILD_ID` (bot
   host). Full six-field ask: `control/outbox.md` entry 2026-07-12T21:05Z.
   - WHERE: Railway dashboard → project `superbot-mineverse` → service
     `web` → Variables (bot-side names on the bot host).
   - RISK: ↩️ reversible — delete a variable to undo; fail-closed throughout.
   - VERIFY: `python3 scripts/readiness_check.py` on the host prints SET for
     every name; sign-in works; the action UI leaves TEST-ECONOMY 503 mode.
3. **Run the real-endpoint conformance e2e once the write pair is set**
   (env-gated — nothing an agent can run without §C.2).
   - WHERE: on the configured host,
     `python3 scripts/conformance_run.py --probe-ingest`
     (runbook: `docs/conformance-runbook.md`).
   - RISK: ✅ safe — test-guild economy only, honest PASS/FAIL verdict.
   - VERIFY: the runner prints PASS; results land in its `--results-dir`.
4. **Add `pytest` as a required status check on superbot-idle main**
   (carried OA-003 — GREEN≠TESTED on idle; full six-field ask:
   `control/outbox.md` entry 2026-07-13T14:56Z, VENUE: hub).
   - WHERE: GitHub → superbot-idle → Settings → Branches (or Rulesets) →
     `main` rule → "Require status checks to pass" → add `pytest` alongside
     `substrate-gate` + `theme-gate`.
   - RISK: ↩️ reversible — remove the context to undo.
   - VERIFY: the next idle PR shows `pytest` in its required-checks list.

## D. Five-minute verify-it-yourself tour

1. *(1 min)* Clone + `pip install jsonschema` + `python3 -m pytest -q` —
   expect **610 passed, 1 skipped** (§B block, first four lines).
2. *(1 min)* `python3 bootstrap.py check --strict` — exit 0: heartbeat fresh,
   docs gates green, no in-progress session cards on main.
3. *(1 min)* `python3 server/app.py`, open <http://127.0.0.1:8000> — miner
   cards, depth race, leaderboard, minimap with ×N co-location badges, all
   rendered from the committed sample; the demo notice (not a false STALE
   alarm) marks it as sample data (PR #100).
4. *(1 min)* `curl -s localhost:8000/api/views | python3 -m json.tool | head`
   — the shaped read; then `curl -si -X POST localhost:8000/api/snapshot/ingest -d '{}'`
   — expect **503** (fail-closed: no secret configured; never a 200).
5. *(1 min)* Skim the audit doc §9 "Top 5 remaining pains" —
   [audits/eap-project-audit-2026-07-14.md](audits/eap-project-audit-2026-07-14.md)
   — each with its paste-ready ask.

## E. Handoff notes (batons — what the next phase needs)

- **Live data flow is one owner action away**: everything in §C.1 + the
  ingest env names in §C.2 turns the committed sample into a live feed; the
  repo side is complete and fail-closed until then.
- **Carried NEXT-2 baton** (`control/status.md` @ `c01c013`): (1) serve the
  games SIM-REQUEST `fishing-full-roster-economy` when the sim verdict
  returns — first full-content-wave batch under ORDER 007's bigger-batches
  rule; (2) verdict-gated waits — fishing cook-leg economy + PRESTIGE tuning;
  consumer-side snapshot-parity work (3 flavor requireds + 7/9 gear slot map)
  stays gated on the pending seam ruling (option A) and lands producer-side
  in product-forge.
- **Honest drops with reasons** are recorded in `control/outbox.md` entry
  2026-07-14T03:46Z (9th hat, slot-map promotion, parity flavor requireds,
  CLAUDE.md re-render) — none should be silently resurrected.
- **Process debt for the next phase**: the substrate-gate added-card
  fail-open ask (`control/outbox.md` entry 2026-07-12T22:10Z, routed to
  substrate-kit) and the audit's ranked asks (§9/§10 of the linked audit)
  are the highest-leverage platform fixes.
- Standing rules that survive the EAP: ORDER 007 (full-content-wave
  SIM-REQUESTs; production-grade mission; correctness outranks speed) and
  the model-attribution ground truth (family-level `📊 Model:` self-report,
  ORDER 001 / Q-0262).
