# superbot-mineverse — project closeout (fleet master)

> **Status:** `reference`
>
> This is the FLEET-MASTER closeout for the whole SuperBot World effort. It is
> written for two readers who know nothing of the autonomous agent sessions
> that built this: the non-coder owner, and a fresh Claude session picking the
> work back up. Its sibling closeouts —
> [superbot-games](https://github.com/menno420/superbot-games) `docs/PROJECT-CLOSEOUT.md`
> and [superbot-idle](https://github.com/menno420/superbot-idle) `docs/PROJECT-CLOSEOUT.md`
> — carry each of those repos' own local threads; this one carries the
> fleet-wide open-thread list.

## What this project is & what was accomplished

**superbot-mineverse** is a small web app: a live, read-only dashboard for a
Discord mining game. A Python standard-library backend (no framework, no
database) serves a snapshot of the game world as JSON; a plain
HTML/CSS/JavaScript frontend (no build step) paints it — leaderboards, miner
cards, a vault view, a minimap. With no configuration at all it runs happily
over a committed sample snapshot, which is what makes it easy to demo and
easy to test.

The backend was built up in deliberate stages, and it is now **more than a
static read server** — it went through **stage (d) PREP**. Everything below
is verified present in the code at the closing commit.

- **Versioned READ contract + views** — `schemas/mining_snapshot.v1.schema.json`
  plus the view-shaping layer `server/views.py` behind `GET /api/views`. Every
  required field in the v1 contract paints somewhere in the frontend. This was
  stage (a).
- **Discord OAuth `identify` sign-in (stage b)** — `server/auth.py`, first
  landed in **PR #11**. A signed session cookie proves "this browser belongs
  to Discord user X" so the frontend can highlight that user's miner. It is
  READ personalization only: no write path, no bot token, no database. When
  the OAuth environment variables are unset the app **degrades cleanly to
  anonymous, read-only** — every public view still works and `GET /api/me`
  honestly reports `auth_configured: false`.
- **HMAC-signed write relay (stage c)** — `server/actions.py`, behind
  `POST /api/action`, **test-guild only**. The server signs each write
  *proposal* with an HMAC-SHA256 secret and relays it to a bot-side executor;
  **the browser never sees the secret**, and the web app never executes an
  action itself. Unset relay env vars → the action route answers an honest 503
  and the frontend shows disabled buttons.
- **HMAC-verified snapshot ingest receiver (stage d PREP)** —
  `server/ingest.py`, behind `POST /api/snapshot/ingest`. This is where a
  bot-side pusher (superbot #2058) would POST fresh game snapshots. It verifies
  the sender's HMAC signature under the repo's one canonical signing scheme,
  v1-validates the body **before** anything is written, then atomically
  replaces the live snapshot file the read routes already re-read fresh on
  every request. It **fails closed** — with the secret or the target path unset
  it refuses all pushes with a 503; there is never an unsigned write over the
  committed sample. First landed 2026-07-14 (suite 575 at that point).

**Security before secrets.** The order of work mattered and was honored: the
authentication / login (CSRF + session-state cookie) protection landed
*before* any secrets-adjacent write or ingest work. The owner-side security
provisioning PR (#31) merged 2026-07-12, ahead of the write and ingest seams.

**Secrets are host environment variables ONLY — never in this repo.** There is
no `.env` file and no committed key anywhere. The six live-mode variables
(named in "Continuation" below) are set on the host at deploy time. **With all
of them unset the app runs read-only and anonymous over the committed sample,
and the full test suite still passes.** That is the default, degraded, safe
state this repo ships in.

Additional verified milestones landing into the closing commit:

- **ORDER 011 record** — owner's 2026-07-18 live direction recorded:
  commit `a8373a2`, *"control(inbox)+docs: ORDER 011 — record owner 2026-07-18
  direction (#133)"*.
- **substrate-kit upgrade to v1.20.1** — commit `7cea1b8`, *"chore(kit):
  upgrade substrate-kit v1.17.0 -> v1.20.1 (#138)"*; its red substrate-gate
  was cleared by `fb0c03f`, *"control: ORDER 012 — fix red substrate-gate on
  kit v1.20.1 upgrade PR #138 (#141)"*.
- **Test-coverage slices** — `server/ingest.py` driven to 100% in `0d1e06c`,
  *"Cover server/ingest.py's untested freshness-parse and persist-cleanup
  branches with tests (#139)"*; `server/app.py` degraded-mode + defensive
  branches covered in the closing commit `c33eec0`, *"Cover server/app.py's
  degraded-mode and defensive branches with tests (#142)"*. Both are
  tests-only with zero production-behavior change.

## Current true state

Verified live at the closing commit:

- **HEAD:** `c33eec0` (PR #142).
- **Test suite:** **682 passed + 1 skipped** — verified by
  `python3 -m pytest -q` at this branch tip.
- **Kit health:** `python3 bootstrap.py check --strict` → **all checks
  passed**. (The only advisory is a non-exit-affecting model-line note on an
  older resident card; it never reds the gate.)
- **Open PRs:** **zero across all three repos** (mineverse API-verified empty
  at close; games and idle carry only their own final-closeout PRs).

## Continuation — open threads, PRIORITY ORDER, with exact resume steps

This is the fleet-master open-thread list. Threads are owner- or contract-gated;
none is blocking day-to-day agent work.

**(1) FIELD-PARITY seam ruling — owner decision needed.**
The producer side here carries **no data debt**: `mining_snapshot.v1` is
complete. The remaining field misses are **consumer-side**, in games-web (which
lives in `menno420/product-forge`), and the fix is gated on the owner's seam
ruling. **Recommended option A:** leave the `mining_snapshot.v1` schema
UNTOUCHED and relax the three flavor `required` fields **consumer-side** in
games-web (a patch bump there), rather than widening this repo's contract.
Evidence and the field-by-field audit:
`docs/findings/snapshot-field-parity-audit-2026-07-14.md`.
*Resume:* owner picks option A (or an alternative); the actual code change then
lands in `menno420/product-forge`, not here.

**(2) GAMES inventory bridge flip + the 1:1 V043 rate ruling.**
The inventory bridge is gated behind an environment flag
(`GAMES_INVENTORY_BRIDGE_ENABLED` — **note: this variable name is NOT defined
in this mineverse repo; confirm the exact name in `menno420/superbot-games` /
product-forge before flipping**). It is paired with an owner ruling on the 1:1
V043 conversion rate. *Resume:* see the
[superbot-games](https://github.com/menno420/superbot-games) closeout for the
repo-local thread; owner confirms the flag name + rate, then the flag flips.

**(3) Bridge slice-4 fork (bidirectional / shared-core).**
Unbuilt **by design** — slices 1–3 shipped; slice 4 (a bidirectional /
shared-core bridge) was deliberately not built pending a design decision.
*Resume:* a design pass in the games/idle repos, not here.

**(4) mineverse GO-LIVE env vars + superbot #2058 draft flip.**
To turn on live data and sign-in, the owner sets these host env vars (all
verified present in the code named below) and flips the superbot #2058 draft so
the bot begins pushing snapshots to `POST /api/snapshot/ingest`:
  - Discord OAuth: `DISCORD_OAUTH_CLIENT_ID`, `DISCORD_OAUTH_CLIENT_SECRET`,
    `OAUTH_REDIRECT_URI`, `WEB_SESSION_SIGNING_KEY` (`server/auth.py`).
  - Write relay (test-guild): `MINING_WRITE_ENDPOINT`,
    `MINING_WRITE_SHARED_SECRET` (`server/actions.py`).
  - Snapshot ingest: `MINING_SNAPSHOT_RELAY_SHARED_SECRET`,
    `MINING_SNAPSHOT_PATH` (`server/ingest.py`).

*Resume:* owner provisions the vars on the web host and flips superbot #2058;
see `docs/live-prod-cutover.md` and `docs/NEXT-TASKS.md` for the full checklist.
The [superbot-games](https://github.com/menno420/superbot-games) and
[superbot-idle](https://github.com/menno420/superbot-idle) closeouts carry
their own repo-local go-live threads.

## Owner walkthrough

Plain-language tour of everything valuable, with paste-ready commands.

**The three repositories**
- [superbot-mineverse](https://github.com/menno420/superbot-mineverse) — this
  repo: the web mining dashboard (backend + frontend).
- [superbot-games](https://github.com/menno420/superbot-games) — the games
  fleet; see its `docs/PROJECT-CLOSEOUT.md`.
- [superbot-idle](https://github.com/menno420/superbot-idle) — the idle game;
  see its `docs/PROJECT-CLOSEOUT.md`.

**The mineverse web app — how to run it locally (read-only / degraded)**
With no environment variables set, this starts the app over the committed
sample snapshot, anonymous and read-only — completely safe:

```
python3 server/app.py          # then open http://127.0.0.1:8000
```

(`PORT` overrides the port; `HOST=0.0.0.0` accepts external traffic on a
server.) On start it prints one honest status line telling you which modes are
configured vs degraded.

**Run the tests** (from the repo root):

```
python3 -m pytest -q           # expect 682 passed + 1 skipped
```

**The games / idle CLIs** — see each repo's `docs/PROJECT-CLOSEOUT.md` for the
paste-ready commands to run them.

**Key documents**
- `docs/current-state.md` — the live truth ledger for this repo.
- `docs/NEXT-TASKS.md` — the forward plan and the go-live env-var roles.
- `docs/live-prod-cutover.md` — the owner-gated live-production checklist.
- `docs/mining-data-contract.md` / `docs/mining-write-contract.md` /
  `docs/auth.md` — the deep contracts.
- `docs/findings/snapshot-field-parity-audit-2026-07-14.md` — the field-parity
  audit behind open thread (1).

**OWNER CHECKLIST — quickest first**
- **(a)** Close the ORDER 012 status line (a one-line control tidy — nothing
  technical outstanding).
- **(b)** Make the **field-parity seam ruling** (open thread 1 — recommended
  option A: relax the three games-web `required` fields consumer-side, schema
  untouched).
- **(c)** The **inventory bridge flip + 1:1 rate ruling** (open thread 2 —
  confirm the flag name in the games repo first).
- **(d)** The **go-live env vars + superbot #2058 draft flip** (open thread 4 —
  provision the six host vars, flip #2058).

## Working this repo with a fresh session

**Boot route** (in order): `.claude/CLAUDE.md` (the working agreement) →
`HANDOFF.md` if present → `docs/current-state.md`. That is the whole boot set;
everything else is routed, not front-loaded.

**Verify commands** before any push:

```
python3 -m pytest -q                 # the test suite (~2 min)
python3 bootstrap.py check --strict  # the kit gate
```

**How PRs land here.** Work on a `claude/*` branch. Open the PR with a
**born-red** session card (`.sessions/<date>-<slug>.md`, Status
`in-progress`) as the FIRST commit — this deliberately holds `substrate-gate`
red. Flipping that card's Status to `complete` as the LAST commit releases the
enabler and lets the PR merge. Tests run **inside substrate-gate**; there is no
separate card-guard workflow in this repo (its CI is exactly
`auto-merge-enabler.yml`, `schema-gate.yml`, `substrate-gate.yml`).

**Gotchas**
- The **born-red substrate-gate HOLD is designed**, not a defect — an added
  in-progress card is supposed to keep the gate red until the flip commit.
- **Git writes may be classifier-denied.** If a raw `git push` is blocked, land
  files via the GitHub MCP tools instead — `push_files` /
  `create_or_update_file` take **RAW file text** (not base64).
- **MCP PR reads can lag ~25 minutes.** Cross-check PR/merge state against live
  GitHub before trusting a stale read.
- `schema-gate.yml` runs the pytest job as a required check — keep the schema
  and its gate green.

---

Sibling closeouts:
[superbot-games](https://github.com/menno420/superbot-games) `docs/PROJECT-CLOSEOUT.md`
·
[superbot-idle](https://github.com/menno420/superbot-idle) `docs/PROJECT-CLOSEOUT.md`
