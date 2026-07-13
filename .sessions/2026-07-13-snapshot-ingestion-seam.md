# Session — 2026-07-13 — snapshot ingestion seam (FLAG 1 consume side)

> **Status:** `complete`
> **Branch:** `claude/snapshot-ingestion-seam`
> **Venue:** lane worker session (ORDER 004 night run — item 5, consume side
> of the bot-lane FLAGs).

**Goal:** build the consume-side ingestion seam for the bot READ relay
(FLAG 1 in `control/status.md`): a `MINING_SNAPSHOT_PATH` host env var that,
when set, points the server at a live-fed snapshot file instead of the
committed `data/sample_snapshot.json`; unset → existing behavior
byte-identical (degraded-by-default doctrine, same pattern as the six
OAuth/write vars). Runtime v1 validation (`server/snapshot_validation.py`)
and per-request fresh reads already exist at all four load paths and are NOT
rebuilt — an invalid/missing live-fed file keeps answering the existing
honest 503. Committed fixtures (valid bot-shaped snapshot distinct from the
sample + invalid: schema violation, corrupt JSON, wrong version) + tests for
the seam; docs env-var names updated (names only, never values).

## Close-out

Shipped on `claude/snapshot-ingestion-seam`. `server/app.py` gained
`ENV_SNAPSHOT_PATH = "MINING_SNAPSHOT_PATH"` + `snapshot_path_from_env()`
(empty string counts as UNSET, mirroring `WriteConfig.from_env`'s
`or None`; the path is deliberately NOT existence-checked at boot so a
set-but-missing feed surfaces as the per-request honest 503, never a
silent boot-time fallback to sample data). `make_server`'s
`snapshot_path` default flipped `SNAPSHOT_PATH` → `None` → resolved via
`snapshot_path_from_env()` — the same defaults-from-env pattern as
`auth_config`/`write_config`, so `main()` picks the seam up with zero
extra plumbing (an explicit argument always beats the environment, so
every existing test/embedder is immune); `main()` prints the snapshot
source mode (`committed sample` vs `live-fed (MINING_SNAPSHOT_PATH)`)
alongside the sign-in/write mode lines. Nothing else in the server moved:
per-request fresh reads + runtime v1 validation at all four load paths
(`_snapshot_is_valid`) already were the hard part and were not rebuilt.

**No last-good in-memory fallback — declined deliberately.** The server
is contractually stateless (docs/architecture.md: "the server holds no
mutable state") and per-request fresh reads are the shipped semantics; a
last-good cache would add mutable state and a staleness surface to keep
honest, trading an honest 503 outage for stale-data risk on the very
first live-fed night. Default stands: invalid/missing live feed → 503 on
every read route, verified fresh each request.

Fixtures: `tests/fixtures/` (new dir) — `live_snapshot_valid.json`
(bot-shaped, guild `555000111222333444`, two miners, distinct from the
sample; pinned conformant under BOTH the runtime interpreter and the real
jsonschema validator), `live_snapshot_wrong_version.json`
(`schema_version: "2"`), `live_snapshot_schema_violation.json` (numeric
snowflake + non-list miners), `live_snapshot_corrupt.json` (truncated
bytes). Coverage: 14 new tests in `tests/test_snapshot_validation.py` —
fixture-honesty units, `snapshot_path_from_env` units (unset/empty/set),
and HTTP seam tests through `serve()` with NO explicit `snapshot_path`
(i.e. the exact `main()` resolution path): unset → sample, valid fixture
→ served on both read routes, missing file → 503, each invalid fixture →
503 on both routes, explicit-arg-beats-env, and a live-rewrite test
pinning fresh-reread + no-last-good (feed flips valid→valid→corrupt;
responses track the file, ending in 503). Suite: **451 passed + 1
conditional skip** (baseline 437 + 14 new); `bootstrap.py check --strict`
red only on this card's own born-red hold until this flip.

Docs (names only, never values): `docs/current-state.md`
degraded-by-default paragraph now names `MINING_SNAPSHOT_PATH`;
`docs/live-prod-cutover.md` §1 notes it is related but NOT one of the six
write-flag prerequisites, and §4 gained the "kill the live snapshot feed"
rollback lever (unset → committed sample, honestly demo-static).
**`scripts/readiness_check.py` unchanged — flagged call:** its exit-0
contract is "all REQUIRED vars SET" and `MINING_SNAPSHOT_PATH` is
optional at every stage (unset is a fully supported mode), so adding it
would either falsely fail ready hosts or need a new "optional" reporting
tier — out of scope tonight, noted in the PR body.

## 💡 Session idea

`server/app.py` now repeats the same load-validate-or-503 block at all
four snapshot load paths (`_serve_snapshot`, `_serve_views`, `_serve_me`,
`_serve_action`): `json.loads(self.snapshot_path.read_bytes())` in a
try/except → 503, then `_snapshot_is_valid` → 503. A fifth load path
could forget one half. Guard recipe: extract one
`_load_valid_snapshot(self) -> tuple[bytes, dict] | None` helper (returns
raw payload too — `_serve_snapshot` ETags the exact bytes — and sends the
503 itself on None), collapse the four sites onto it, verified by the
HTTP sections of `tests/test_snapshot_validation.py` and the
malformed-snapshot tests in `tests/test_server_robustness.py` staying
green at 451 + 1 skip.

## ⟲ Previous-session review

The `2026-07-12-seasonal-decorations` card is a model build close-out:
the pure/impure split is stated as a contract (date INJECTED, one impure
boot caller), every judgment call is recorded WITH its tradeoff
(local-vs-UTC wall-calendar choice flagged honestly), and the exhaustive
all-days sweep is exactly the cheap overkill that makes a date-window
feature boring. Its 💡 idea (`pixelSVGShell` dedupe of the four
hand-concatenated `<svg>` shells) carries a proper guard recipe and is
still unlanded — a good micro-slice for a quiet slot, and this session's
own idea is the same shape on the server side (four duplicated snapshot
load blocks), which suggests the dedupe-behind-one-seam pattern is the
repo's recurring cleanup class. Carried nit, now four reviews running:
the bare-`📊 Model:`-line housekeeping sweep on the older 2026-07-12
cards has still neither landed nor been explicitly dropped — the next
records pass should do one or the other.

- **📊 Model:** fable-5 · standard effort · task-class: FLAG-1 consume-side snapshot ingestion seam — MINING_SNAPSHOT_PATH env seam + fixtures (build)
