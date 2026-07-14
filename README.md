# superbot-mineverse

A browser game over the live mining economy of the [superbot](https://github.com/menno420/superbot)
Discord bot. Players will eventually watch — and later steer — their real miners
from a web page, while the bot itself stays the only thing that can touch the
real data.

## Safety architecture (the rules that never change)

- The web app **never touches Postgres** and **never holds the bot token**.
- Reads arrive via a **versioned mining data contract**: the bot projects its
  miner state into a read relay; this app consumes only that projection.
- Writes (future, test-guild first) go **only** through a bot-side **audited
  action endpoint** — the web app never mutates anything directly.
- This repo contains **no database and no secrets**. The optional Discord
  sign-in (stage b) proves identity for read personalization only — its
  credentials live exclusively in host env vars (`docs/auth.md`).

## Staged ladder

| Stage | What | Status |
| --- | --- | --- |
| 0 | Walking skeleton: sample snapshot → stdlib server → static frontend | **done** (merged PR #2) |
| a | Read contract v1: versioned mining data contract, bot-side projection | **done** (merged PR #7) |
| b | Discord OAuth per-player read | **done** (this stage — see [Discord sign-in](#discord-sign-in-stage-b)) |
| c | Write contract v1 — test-guild only, via the bot's audited action endpoint | **done** (contract merged PR #13; shim + action UI — see [Web actions](#web-actions-stage-c--test-economy-only); the real bot-side endpoint is built in the superbot repo against `docs/mining-write-contract.md`) |
| d | Live-prod prep, owner-flag-gated | **prepared** (cutover checklist `docs/live-prod-cutover.md` + mechanical readiness check `scripts/readiness_check.py`; the owner's live-guild flag stays OFF) |

The reads are degraded-by-default: with no configuration everything renders
from a committed sample payload whose field names follow the versioned data
contract (mirroring superbot's real miner state — `mining_player_state` +
`game_xp_service`); with `MINING_SNAPSHOT_PATH` set the same routes serve the
live-fed snapshot file instead, re-read fresh on every request.

## Run it locally

```
python3 server/app.py          # http://127.0.0.1:8000  (PORT env overrides)
```

- `GET /api/snapshot` — the snapshot as JSON: the committed sample
  (`data/sample_snapshot.json`) by default, or the live-fed file when
  `MINING_SNAPSHOT_PATH` is set
- `GET /api/views` — the same snapshot shaped for the frontend (this is the
  route the frontend actually renders from: panels, depth ladder,
  leaderboards, inventory, staleness)
- `GET /api/me` — who is signed in (and their miner from the snapshot, if any)
- `POST /api/action` — stage-c write relay: signs and forwards a proposal to
  the bot-side executor (TEST ECONOMY only; honest 503 when not configured)
- `POST /api/snapshot/ingest` — receive side of the bot→web READ relay:
  HMAC-verified push, v1-validated, atomically persisted (honest 503 when not
  configured)
- `/auth/login` · `/auth/callback` · `/auth/logout` — Discord OAuth sign-in
- `/` — static frontend: your miner (when signed in), miner cards, a depth
  race, and a leaderboard

Run the tests (no secrets, no network needed):

```
python3 -m pytest -q
```

Operational checks for a configured host (both print env-var NAMES and
SET/UNSET only — never a value):

```
python3 scripts/readiness_check.py --probe-ingest   # cutover readiness + one unsigned probe of the ingest route (expects 401/503, never 200)
python3 scripts/conformance_run.py                  # one-command WRITE-contract conformance sweep against the real executor
```

## Discord sign-in (stage b)

Signing in with Discord (`identify` scope only) personalizes the read-only
view: the frontend shows *your* miner — matched by your Discord user id
against `miners[].suid` in the snapshot — front and center. It grants no
write ability of any kind; full flow, cookie format, and threat notes:
[`docs/auth.md`](docs/auth.md).

Configuration comes from **host environment variables only** — never from
files in this repo:

| Env var | Meaning |
| --- | --- |
| `DISCORD_OAUTH_CLIENT_ID` | Discord application client id |
| `DISCORD_OAUTH_CLIENT_SECRET` | Discord application client secret |
| `OAUTH_REDIRECT_URI` | the `/auth/callback` URL registered with Discord (https turns on the `Secure` cookie flag) |
| `WEB_SESSION_SIGNING_KEY` | HMAC key for the CSRF state + session cookie |

**Degraded mode**: with any of them absent (CI, fresh local clones) the app
runs exactly as before — all public views work, `GET /api/me` reports
`auth_configured: false`, `/auth/login` answers an honest 503, and the
frontend shows a disabled "sign-in not configured" button. The full test
suite passes with no secrets present.

## Web actions (stage c) — TEST ECONOMY only

Signed-in players get action buttons (mine, descend, ascend, sell, vault
deposit/withdraw, equip) on the "My miner" view. A click never writes
anything from here: the browser sends `{action_id, action, params}` to
`POST /api/action`, and this server derives the actor from the verified
session cookie, signs the PROPOSAL with a secret the browser never sees,
and relays it to the bot-side executor — full contract:
[`docs/mining-write-contract.md`](docs/mining-write-contract.md).

Configuration comes from **host environment variables only**:

| Env var | Meaning |
| --- | --- |
| `MINING_WRITE_ENDPOINT` | full URL of the bot-side action endpoint (dev: the shim — `python3 -m tests.shim.shim_bot`) |
| `MINING_WRITE_SHARED_SECRET` | HMAC key signing every proposal (shared with the bot side) |

**Degraded mode** (the default — CI, fresh clones): with either absent,
the buttons render disabled ("writes not configured — read-only mode"),
`POST /api/action` answers an honest 503, and everything else works
exactly as before. When writes ARE configured, a persistent **TEST
ECONOMY** badge shows in the header — v1 is hard-allowlisted to test
guilds; live guilds are rejected until the owner's stage-d flag.

## Live snapshot relay (READ side)

The bot can push its real snapshot to `POST /api/snapshot/ingest`; the read
routes then serve that file instead of the committed sample. Configuration is
**host environment variables only** (names listed here; values never live in
this repo):

| Env var | Meaning |
| --- | --- |
| `MINING_SNAPSHOT_PATH` | file the verified push is persisted to, and the file the read routes serve |
| `MINING_SNAPSHOT_RELAY_SHARED_SECRET` | HMAC key the bot-side pusher signs every push with |

**Degraded mode** (the default): with either absent, ingest answers an honest
503 and the app serves the committed sample exactly as before. Fail closed —
unsigned data is never accepted, and the committed sample is never overwritten.

## Repo layout

| Path | What |
| --- | --- |
| `data/` | committed sample snapshot JSON — the default data source (a live-fed `MINING_SNAPSHOT_PATH` file replaces it at runtime, never in the repo) |
| `server/` | stdlib-only Python 3.10 backend: JSON API (snapshot, views, me, action relay, snapshot ingest), Discord OAuth, static file serving |
| `web/` | vanilla HTML/JS/CSS frontend, no build step |
| `schemas/` | versioned contract JSON Schemas: read (`mining_snapshot.v1.schema.json` ↔ `docs/mining-data-contract.md`) + write (`mining_action.v1.schema.json`, `mining_action_response.v1.schema.json` ↔ `docs/mining-write-contract.md`) |
| `tests/` | pytest: API routes + payload sanity |
| `control/` | fleet coordination bus: manager orders in, session status out |
| `docs/` | working agreements, architecture, current state, capabilities |

Layering is strict and flows one way: `data/ -> server/ -> web/`. The frontend
talks to the backend only via the JSON API and never reads `data/` directly;
the server never writes.

## For agents

Orientation reading order: `.claude/CLAUDE.md` (working agreement) →
`docs/current-state.md` → `docs/CAPABILITIES.md` → `docs/AGENT_ORIENTATION.md`.
Coordination conventions live in `control/README.md`. Verify every change with
`python3 -m pytest -q` before pushing.
