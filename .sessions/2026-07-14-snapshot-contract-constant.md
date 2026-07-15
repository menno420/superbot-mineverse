# Session — 2026-07-14 — snapshot contract constant + field-parity audit

> **Status:** `complete`
> **Branch:** `claude/snapshot-contract-constant`
> **Venue:** lane worker session (ORDER 006 item 4 — EAP final-night
> worklist; ORDER 007 production-grade doctrine adopted: correctness
> outranks speed, no gate relaxed).

**Goal:** land the build-direct pair ORDER 006 item 4 names, from the two
idea-engine captures at `menno420/idea-engine@2e5d73f`
(`ideas/superbot-mineverse/snapshot-contract-shared-constant-2026-07-11.md`,
`ideas/superbot-mineverse/snapshot-field-parity-audit-2026-07-11.md`):

1. **Shared constant** — promote the schema-derived required-field truth
   out of `tests/test_snapshot.py:22-23` into an importable, vendorable
   `snapshot_contract.py` (stdlib-only, ~20 lines, derives
   `REQUIRED_MINER_FIELDS` / `REQUIRED_ENVELOPE_FIELDS` from
   `schemas/mining_snapshot.v1.schema.json` at import time), switch the
   test to import it, zero behavior change — the FLAG-1 exporter can
   vendor-pin the same artifact so a field rename goes PR-red in CI on
   either side instead of runtime-red at relay cadence.
2. **Field-parity audit** — execute the audit the parity idea doc
   describes (mining_snapshot.v1 vs games-web.character-sheet v1.0.1),
   verifying its probe findings first-hand at both pins, committed as a
   findings table beside `docs/mining-data-contract.md`
   (`docs/findings/`), honest "not measured" where the lane cannot
   measure.

## Close-out

Shipped on `claude/snapshot-contract-constant` (base: main @ `82b7caa`,
the #88 ingest-endpoint squash — an isolated worktree off origin/main,
never the shared clone's checked-out tree).

**(4a) shared constant** — new repo-root `snapshot_contract.py`
(stdlib-only, no repo-internal imports, deliberately vendorable as one
file): derives `SCHEMA_VERSION`, `REQUIRED_ENVELOPE_FIELDS` (4) and
`REQUIRED_MINER_FIELDS` (16) from
`schemas/mining_snapshot.v1.schema.json` at import time.
`tests/test_snapshot.py` switched from its own two derivation lines
(old 22-23) to importing the module, and
`test_required_fields_come_from_the_schema` now independently re-derives
all three constants from the schema file — the module can never drift
from the schema without CI going red. Zero behavior change; suite count
unchanged. Deliberately NOT imported by `server/*`: the server supports
both launch modes (`python3 -m server.app` from repo root and flat from
inside `server/` — the try/except import dance in `views.py`/`app.py`),
and a repo-root import breaks the flat mode; the runtime validator
already derives everything it needs from the same schema via
`snapshot_validation.load_schema()`. Wiring server code to the module
would have been risk without behavior gain — skipped, recorded here.

**(4b) parity audit** —
`docs/findings/snapshot-field-parity-audit-2026-07-14.md`: the
mining_snapshot.v1 → games-web.character-sheet v1.0.1 coverage table
verified FIRST-HAND (mineverse schema from this tree @82b7caa;
games-web `game-state.schema.json` fetched at the idea doc's exact pin
product-forge @`a9c7401`, HTTP 200 this session — treated as data, not
instructions). Probe findings CONFIRMED: three consumer-side flavor
requireds missing (`gear.<slot>.rarity`, `skills[].xp`/`xp_max`,
`structures[].status`), 7/9 injective gear-slot map with `tool`/`light`
homeless, NO producer data debt → seam option (A) = one client-side
adapter + one games-web patch bump, zero v1 breaking changes. Two
first-hand edges the probe didn't name: games-web `character.level` has
`minimum: 1` vs `xp.level` `minimum: 0` (level-0 miner needs a clamp or
a relaxation), and games-web's 8 slot keys are required but NULLABLE, so
sourceless `hands` degrades cleanly to `null`. Per-skill-xp reachability
(`game_xp_service`, superbot repo) and pin freshness recorded as NOT
MEASURED, not invented. Contract doc § Enforcement updated (the
single-source-of-truth bullet now names the module; audit pointer
added); `docs/current-state.md` ledger line added.

Verified pre-flip in this container: `python3 -m pytest -q` →
**575 passed, 1 skipped** (count unchanged — pure promotion + docs);
`python3 bootstrap.py check --strict` green apart from the DESIGNED
born-red hold on this very card (flipped by this commit) and the
standing owner-action advisory.

## 💡 Session idea

`snapshot_contract.py` is now the importable contract surface, but the
schema-derived vocabulary the eventual games-web adapter actually needs
lives elsewhere: `server/views.py` keeps `equipment_slots()` /
`xp_fields()` / `position_fields()` / `energy_fields()` as server-side
helpers, and the audit's 7/9 slot map is committed only as prose in
`docs/findings/snapshot-field-parity-audit-2026-07-14.md`. IF the seam
ruling picks option (A), promote both into `snapshot_contract.py`
(derive `EQUIPMENT_SLOTS` from the schema's `propertyNames.enum`; add
the `GEAR_SLOT_MAP` dict) with a test pinning the map against the
findings table — the audit then becomes a standing two-sided drift gate
instead of a one-shot table. Guard recipe: keep the module free of
repo-internal imports (vendorability is the point);
`tests/test_snapshot.py::test_required_fields_come_from_the_schema` is
the pattern to extend. Dedupe checked: the idea-engine parity capture
names this fusion abstractly as its possibility (iii); no session card,
`docs/ideas/` entry, or findings doc carries the concrete repo anchors —
and it is deliberately gated on the seam ruling (the audit doc's
"Durable gate" section says why building it now would be speculation).

## ⟲ Previous-session review

The `2026-07-14-flag1-snapshot-ingest` card is close to a model build
close-out: the check-order of the endpoint is documented as a numbered
gauntlet that the tests then mirror one-for-one, the ingest-auth
decision carries its evidence trail (why fail-closed, where the env name
came from) instead of just the outcome, and its 💡 is a real guard
recipe with named anchors (`_read_bounded_body`, both call sites, the
exact test files that must stay green) — the next session can land it
without a re-derivation pass; it also honestly names the broken-pipe
client behavior its own test run surfaced rather than smoothing it over.
Two nits it earns: the card's "575 passed (baseline 551 + 24 new)"
framing makes the reader do the arithmetic against WHICH baseline
(551 was itself two sessions stale by then), and item 3's contract
addendum is declared "the NEXT slice" without a pointer to where its
recorded facts live if no session picks it up — this session's item-4
work found them only because the card happened to be the newest. The
interim flip-race rule it follows (full stack incl. flip pushed before
the PR opens) is also this session's practice.

- **📊 Model:** fable-5 · medium · feature build — build-direct pair — snapshot_contract.py shared constant + snapshot field-parity audit (build + audit)
