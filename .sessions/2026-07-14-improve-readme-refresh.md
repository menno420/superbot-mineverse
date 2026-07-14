# Session — 2026-07-14 — README refresh to HEAD reality

> **Status:** `complete`
> **Branch:** `claude/improve-readme-refresh`
> **Venue:** improvement-wave lane E (owner directive 2026-07-14: "See if
> there is anything else you can come up with or improve"; wave claim
> `control/claims/claude-improvement-wave-2026-07-14.md`, merged #95).

**Goal:** bring `README.md` back in line with the code at HEAD
(harvest at `58657ed`). Verified drift: :29 still says "Stage 0
(current code)" although the live-fed `MINING_SNAPSHOT_PATH` seam
exists (server/app.py:6-15); the :40-44 endpoint list omits
`GET /api/views` (the route the frontend actually renders from,
web/app.js:1858), `POST /api/action` (server/app.py:112) and
`POST /api/snapshot/ingest` (server/app.py:113); the ladder :27 calls
stage d "planned" while it is PREPARED (docs/current-state.md:33-34:
cutover checklist + readiness check); the :105 repo-layout row
describes `server/` as snapshot+static only. Fix those, add the two
snapshot-relay env-var NAMES only (`MINING_SNAPSHOT_PATH`,
`MINING_SNAPSHOT_RELAY_SHARED_SECRET` — server/ingest.py:54,57; never
values), and one quickstart line each for
`scripts/readiness_check.py --probe-ingest` and
`scripts/conformance_run.py`. Docs-only; README.md at repo root is
outside the docs-gate badge scan (bootstrap.py `check_badges` walks
the docs root only), so no Status badge needed.

## Close-out

Shipped on `claude/improve-readme-refresh` (base: main @ `cdec736`, the
#95 wave-claim squash atop `58657ed`). README-only diff, every claim
cross-checked against HEAD before writing:

- Ladder stage d: "planned" → **prepared**, citing
  `docs/live-prod-cutover.md` + `scripts/readiness_check.py`
  (docs/current-state.md:33-34; the owner flag stays OFF).
- The stale "Stage 0 (current code)" paragraph now states the real
  degraded-by-default read path: sample by default, live-fed
  `MINING_SNAPSHOT_PATH` file when set, re-read per request
  (server/app.py:6-15).
- Endpoint list grew the three missing routes with one-line honest
  descriptions: `GET /api/views` (the route the frontend renders from —
  web/app.js:1858), `POST /api/action`, `POST /api/snapshot/ingest`
  (route constants server/app.py:109-113).
- New "Live snapshot relay (READ side)" section: the two env-var NAMES
  only (`MINING_SNAPSHOT_PATH`, `MINING_SNAPSHOT_RELAY_SHARED_SECRET`
  — server/ingest.py:54,57), degraded/fail-closed behavior spelled out;
  no value, no URL.
- Quickstart block: one line each for
  `scripts/readiness_check.py --probe-ingest` (readiness_check.py:38)
  and `scripts/conformance_run.py` (conformance_run.py:36-38), with the
  names-only/SET-UNSET hygiene stated.
- Repo-layout rows for `data/` and `server/` updated to HEAD reality
  (server/ = 7 modules: API incl. views/action/ingest, OAuth, static).

Docs-gate check: README.md at repo root is OUTSIDE the badge scan —
`bootstrap.py check_badges` walks `_md_files(docs_root)` only
(bootstrap.py:1593-1613) — so no Status badge added; `check --strict`
confirms exit 0.

Verified pre-flip in this container: `python3 -m pytest -q` →
**587 passed, 1 skipped** (docs-only, baseline unchanged);
`python3 bootstrap.py check --strict` exit 0 (tails in the PR body).

## 💡 Session idea

README endpoint-list drift guard: this session fixed three routes the
README had silently dropped; nothing stops the fourth. Add a small test
that reads `README.md` and asserts every route constant exported by
`server/app.py` (`API_SNAPSHOT`, `API_VIEWS`, `API_ME`, `API_ACTION`,
`API_SNAPSHOT_INGEST` — app.py:109-113) appears in the "Run it locally"
endpoint list, so adding a route without documenting it reds CI with a
one-line fix. Guard recipe: plain file-read + `from server import app`
(sys.path pattern of tests/test_achievements.py:17-20); assert
`route in readme_text` per constant. Dedupe checked: no `tests/*` file
references README today (grep), no `docs/ideas/` entry or session card
proposes a README pin — the 2026-07-11 enforce-pytest-gate card touched
the repo-layout table but added no guard.

## ⟲ Previous-session review

The `2026-07-14-readiness-ingest-leg` card holds up well under replay:
its riskiest security claim (unsigned 200 = FAILURE, 401/503 = the only
honest answers) is anchored to real code (`INGEST_401_REASONS`
transcribing `server/actions.verify`'s two returns), and its verify
line (587 passed + 1 skipped) matches exactly what this session
measured at HEAD before touching anything — the numbers were real, not
aspirational. Its 💡 (conformance_run ingest leg via the importlib
loader) remains valid and unclaimed: `scripts/conformance_run.py` still
contains zero mentions of ingest as of `cdec736`, so the idea has not
rotted — but that is also its weakness, echoing the critique that card
itself made of its predecessor: the idea names consumer file and test
pattern, yet three sessions later no lane has picked it up, which
suggests naming a file is necessary but not sufficient — wave-style
coordinator directives (like today's) may be the only reliable
consumer for gated ideas. One nit: that card's close-out says "tail
pasted in the PR" for bootstrap but records no finding counts in the
card itself, so a reader auditing from cards alone cannot see the
advisory-finding surface it left behind.

- **📊 Model:** fable-5 · standard effort · task-class: README refresh to HEAD reality — endpoint list, stage ladder, layout row, relay env names, script quickstarts (docs-only)
