# superbot-mineverse — next tasks

> **Status:** `plan`
>
> The prioritized next-step menu for this repo, written for the 2026-07-17
> fresh-start (the Claude Code Projects EAP goes read-only 2026-07-21 and the
> owner is recreating this project fresh). This replaces the retired
> `control/` message-bus + wake-chain apparatus as the forward-plan surface.
> Live status: `docs/current-state.md`. **Green `claude/*` PRs land
> automatically on green CI** — agents open ready with green CI and the
> enabler workflow's GitHub-native auto-merge lands the head SHA itself; the
> owner never reviews unmerged PRs (see `docs/decisions.md` and
> `CONSTITUTION.md`).
>
> **What this app is:** a read-only browser dashboard / companion web app over
> superbot's live **mining** economy (miner cards, depth/biome ladder,
> leaderboards, guild inventory, minimap) plus an audited, HMAC-signed
> action-relay. It never touches Postgres or the bot token; it consumes a
> versioned snapshot contract. It is a data-viewer, not a game engine.

## Owner-gated go-live items (host env vars — NAMES ONLY, values are the owner's)

None of these live in the repo. They are Railway host env vars the owner sets
in the console; with all unset the app runs read-only + anonymous over the
committed sample and the full test suite passes (degraded-by-default). Provision
is an **owner action** — agents cannot set secrets. Set them, then re-run the
env-gated conformance probe (`scripts/conformance_run.py --probe-ingest`).

1. **Discord OAuth sign-in** (stage b — personalizes the read view only, grants
   zero write ability). Four host vars; with any unset, `/auth/login` returns an
   honest 503 and the site stays anonymous:
   - `DISCORD_OAUTH_CLIENT_ID`
   - `DISCORD_OAUTH_CLIENT_SECRET`
   - `OAUTH_REDIRECT_URI` (an `https` value turns on the Secure cookie flag)
   - `WEB_SESSION_SIGNING_KEY` (HMAC key signing the session + CSRF `state`
     cookie — this **is** the auth-gate signing key; there is no separate
     password. The site has NO site-wide login gate; it is public + read-only.)

2. **Mining WRITE relay** (stage c — test-guild only; server signs, browser
   never sees the secret). Unset → action buttons render disabled and
   `POST /api/action` returns 503:
   - `MINING_WRITE_ENDPOINT` (bot-side executor URL the relay targets)
   - `MINING_WRITE_SHARED_SECRET` (HMAC key signing every write proposal;
     shared with the bot side)

3. **Snapshot INGEST relay** (FLAG 1 — the live READ feed; fail-closed 503
   without BOTH):
   - `MINING_SNAPSHOT_RELAY_SHARED_SECRET` (HMAC verify of the bot→web push to
     `POST /api/snapshot/ingest`)
   - `MINING_SNAPSHOT_PATH` (persist target; set → serves the live-fed
     snapshot, unset → serves the committed sample)
   - Bot-side counterparts (set on the **bot** host, not this repo):
     `MINING_SNAPSHOT_RELAY_URL`, `MINING_SNAPSHOT_RELAY_GUILD_ID`.

## Next steps (highest-value first)

1. **Wire the live READ feed end-to-end** (the single highest-value unblock):
   flip superbot #2058 out of draft and implement sender-side HMAC signing so
   the bot pushes real snapshots to `POST /api/snapshot/ingest`. The receive
   side is already built + tested (PRs #88 / #93). Verify `staleness.source`
   flips from `sample` to `live`.

2. **Provision the host env vars** above on Railway (OAuth four reportedly
   already set; outstanding: `MINING_WRITE_ENDPOINT` + `MINING_WRITE_SHARED_SECRET`,
   plus the ingest pair), then run `scripts/conformance_run.py --probe-ingest`
   (currently env-gated and unrunnable by an agent).

3. **Build the bot-side WRITE endpoint (FLAG 2)** in the superbot repo: an
   HMAC-signed action-proposal executor with audit + idempotency + a test-guild
   allowlist, so the stage-c action buttons perform real test-guild writes
   against `docs/mining-write-contract.md`.

4. **Multi-guild snapshot UI** (groomed-backlog item 8): the schema envelope is
   single-guild today; add a guild switcher after the contract addition
   (discuss-first).

5. **Consumer-side snapshot field-parity work** (option A from the 2026-07-14
   audit): 3 flavor requireds (`gear.rarity`, `skills[].xp/xp_max`,
   `structures[].status`) + resolve the 7/9 gear-slot map (`tool` / `light`
   homeless) via one client-side adapter + a games-web patch bump.

6. **Stage (d) live-prod cutover** once the owner flips the flag (add prod guild
   ids to the bot-side allowlist + an owner ORDER). The mechanical readiness /
   conformance tooling (`scripts/readiness_check.py`, `docs/live-prod-cutover.md`)
   is already built and owner-flag-gated.

## Retired with the wind-down (do not act on / do not re-arm)

- The `control/` message bus (`inbox.md` / `outbox.md` / `status.md` /
  `README.md` + `claims/`) — coordination scaffolding, kept as history only.
- Wake-chain routines / failsafe crons (`docs/ROUTINES.md`) — do NOT re-arm;
  any trigger still armed for this seat is the owner's to delete.
- The agent-arms-auto-merge doctrine (agents hand-arming their own merges) —
  retired: agents do not hand-arm auto-merge or REST-merge. But
  `.github/workflows/auto-merge-enabler.yml` itself is **LIVE, not retired** —
  it is the mechanism that lands green `claude/*` PRs: it arms GitHub-native
  auto-merge at open so the green head SHA merges itself. The owner never
  reviews unmerged PRs (see `docs/decisions.md`).
