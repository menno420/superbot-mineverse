# superbot-mineverse

A browser game over the live mining economy of the [superbot](https://github.com/menno420/superbot)
Discord bot. **Stage 1 (current): a read-only walking skeleton** — no auth, no
database, no secrets, no live data. Everything renders from a committed sample
payload whose field names mirror superbot's real miner state
(`mining_player_state` + `game_xp_service`), so a later real data contract is a
drop-in swap.

## Run it

```
python3 server/app.py          # http://127.0.0.1:8000  (PORT env overrides)
```

- `GET /api/snapshot` — the sample snapshot (`data/sample_snapshot.json`) as JSON
- `/` — static frontend: miner cards, a depth race, and a leaderboard

## Layout

| Path | What |
| --- | --- |
| `data/sample_snapshot.json` | committed sample snapshot (the only stage-1 data source) |
| `server/app.py` | stdlib-only backend: JSON API + static file serving |
| `web/` | vanilla HTML/JS/CSS frontend, no build step |
| `tests/` | pytest: API routes + payload sanity |

Layering: `data/ -> server/ -> web/` — the frontend talks to the backend only
via the JSON API; nothing in this repo writes anything.

## Verify

```
python3 -m pytest -q
```

Agent workflow, docs, and coordination conventions: `.claude/CLAUDE.md`,
`docs/`, and `control/README.md`.
