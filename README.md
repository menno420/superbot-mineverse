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
- This repo contains **no database, no auth, no secrets**.

## Staged ladder

| Stage | What | Status |
| --- | --- | --- |
| 0 | Walking skeleton: sample snapshot → stdlib server → static frontend | **done** (merged PR #2) |
| a | Read contract v1: versioned mining data contract, bot-side projection | **next / in progress** |
| b | Discord OAuth per-player read | planned |
| c | Write contract v1 — test-guild only, via the bot's audited action endpoint | planned |
| d | Live-prod prep, owner-flag-gated | planned |

Stage 0 (current code) is read-only end to end: everything renders from a
committed sample payload whose field names mirror superbot's real miner state
(`mining_player_state` + `game_xp_service`), so the stage-a data contract is a
drop-in swap.

## Run it locally

```
python3 server/app.py          # http://127.0.0.1:8000  (PORT env overrides)
```

- `GET /api/snapshot` — the sample snapshot (`data/sample_snapshot.json`) as JSON
- `/` — static frontend: miner cards, a depth race, and a leaderboard

Run the tests:

```
python3 -m pytest -q
```

## Repo layout

| Path | What |
| --- | --- |
| `data/` | committed sample snapshot JSON — the only data source in stage 0/1 |
| `server/` | stdlib-only Python 3.10 backend: `GET /api/snapshot` + static file serving |
| `web/` | vanilla HTML/JS/CSS frontend, no build step |
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
