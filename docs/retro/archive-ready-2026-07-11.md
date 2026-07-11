# Archive-ready note — 2026-07-11

> **Status:** `historical`
>
> Written by the wrap-up session as the coordinator chat's close-out. The
> coordinator conversation is archived after this; everything a future
> session needs is committed — nothing important remains chat-only.

## True state, one paragraph

superbot-mineverse is a complete, green, owner-flag-gated stage-1 web game:
a stdlib-Python read-only backend serving a committed sample snapshot and
derived views, a vanilla HTML/JS/CSS frontend (cave theme, achievements,
share card, easter eggs), READ and WRITE contracts v1 with CI schema gates,
Discord OAuth sign-in and a test-guild-only write relay — both DORMANT in
degraded mode until the owner provisions env vars — and a prepared,
owner-flag-gated live-prod cutover. 39 of 40 PRs merged on green
(PR #31, the owner's own Codex security report, is open awaiting owner
review); the suite is 327 passed + 1 conditional skip;
`bootstrap.py check --strict` is green; orders 001 and 002 are done;
`control/claims/` is empty (README only). All remaining work is externally
blocked on the Builder lane and the owner items below.

## ⚑ Owner actions outstanding

1. **Builder-lane FLAG 1 — READ relay**: the bot must emit a v1-conformant
   snapshot (`schemas/mining_snapshot.v1.schema.json`, prose
   `docs/mining-data-contract.md`). Full spec carried verbatim in
   `control/status.md`.
2. **Builder-lane FLAG 2 — WRITE endpoint**: HMAC-signed action-proposal
   endpoint per `schemas/mining_action.v1.schema.json` — MUST be audited:
   `mining_workflow` emits zero `emit_audit_action` calls today, the
   handler must add it; hard test-guild allowlist. Full spec carried
   verbatim in `control/status.md`.
3. **Owner env vars** (host-side only, names never values):
   `DISCORD_OAUTH_CLIENT_ID`, `DISCORD_OAUTH_CLIENT_SECRET`,
   `OAUTH_REDIRECT_URI`, `WEB_SESSION_SIGNING_KEY`,
   `MINING_WRITE_ENDPOINT`, `MINING_WRITE_SHARED_SECRET` — the first four
   switch sign-in on; the last two (plus FLAG 2) switch test-guild write
   mode on.
4. **Stage-5 live-prod flag** (owner-only, never agent-decided): owner adds
   prod guild ids to the bot-side allowlist AND orders it via
   `control/inbox.md`.
5. **PR #31** — the owner's Codex-authored pre-provisioning security report
   is OPEN; owner reviews/merges it himself (not a claude/* lane).

## Resuming: what a fresh session reads, in order

1. `README.md`
2. `docs/current-state.md`
3. `control/status.md` (+ `control/inbox.md` for new orders)
4. `docs/retro/` — the founding-day retro
   (`2026-07-11-founding-day-retro.md`) and this note.

The groomed backlog is parked at
`docs/ideas/founding-day-groomed-backlog-2026-07-11.md` — nothing in it is
approved or in flight.

## Trigger-disarm record (verbatim, 2026-07-11T19:39Z)

- Cron "superbot-mineverse failsafe wake"
  (`trig_01K8xmAKYS5S2HLy1HPANM7j`, `20 */2 * * *`, bound to coordinator
  session_017yrng4qx2LcLNqKb5AGoe8) — `delete_trigger` tool output,
  verbatim: `deleted trigger trig_01K8xmAKYS5S2HLy1HPANM7j`.
- Pending run_once "superbot-mineverse chain link" triggers bound to
  session_017yrng4qx2LcLNqKb5AGoe8: **none exist** — every chain-link
  trigger in the account's Routine list (paginated fully back past the
  day's first link) shows `ended_reason: "run_once_fired"`; the newest
  (`trig_016avdSjADLLCyPMLsn6uQeX`, 19:31Z) already fired. Nothing to
  delete; nothing will wake the archived coordinator.

## Nothing chat-only

Confirmed at close: the day's history and lessons are in
`docs/retro/2026-07-11-founding-day-retro.md`; capability findings are in
`docs/CAPABILITIES.md`; the ledger is in `docs/current-state.md`; owner
asks and Builder specs are in `control/status.md`; the backlog is in
`docs/ideas/`; session evidence is in `.sessions/`. The archived
coordinator chat contains no unique state.
