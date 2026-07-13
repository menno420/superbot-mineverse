# Finding — snapshot field-parity audit: mining_snapshot.v1 vs games-web.character-sheet v1.0.1

> **Status:** `audit`
>
> Field-by-field coverage audit of this repo's READ contract
> (`schemas/mining_snapshot.v1.schema.json`) against product-forge's
> games-web character-sheet contract, executed lane-side per ORDER 006
> item 4 from the idea-engine capture
> `ideas/superbot-mineverse/snapshot-field-parity-audit-2026-07-11.md`
> (idea-engine @ `2e5d73f`). It feeds the manager's games-web↔mineverse
> seam ruling: it costs seam option (A) — games-web consumes the
> mineverse projection — instead of guessing at it.

## Grounding — both schemas re-read for this audit, not quoted

- **mineverse side:** `schemas/mining_snapshot.v1.schema.json` read from
  this working tree at `82b7caa` (this session's base). Byte-comparison
  point: the idea doc's probe pinned the same file at `2b1bd0b`; the
  envelope `required` list (4 keys) and per-miner `required` list
  (16 fields) are unchanged.
- **games-web side:**
  `products/games-web/data/schema/game-state.schema.json` fetched
  2026-07-13 from `menno420/product-forge` at the probe's exact pin
  `a9c7401856e47974f5fc3f56f45f9cc5c844186f` (raw.githubusercontent.com,
  HTTP 200) — contract `games-web.character-sheet`, `$comment` "Contract
  v1.0.1". This audit did NOT re-verify whether `a9c7401` is still
  product-forge's HEAD; freshness of the pin is the probe's claim, not
  this document's.

## Structural mismatch first (shape, before any field)

`mining_snapshot.v1` is a **per-guild** envelope (`miners[]`, may be
empty); `games-web.character-sheet` renders **one character**. Any
adapter therefore selects one miner and projects it — the audit below is
per-miner-to-character. The envelope's `guild_id` has no games-web home
(dropped by the adapter; games-web's envelope is closed).

## The coverage table (games-web required unless marked opt)

| games-web v1.0.1 field | mining_snapshot.v1 source @ `82b7caa` | class |
|---|---|---|
| `schema_version` (semver pattern) · `contract` (const) | envelope `schema_version` (const `"1"`); `contract` is a self-identifier | serializer-constant |
| `generated_at` | envelope `generated_at` | covered |
| `character.name` | `miner.display_name` | covered |
| `character.level` (min **1**) | `miner.xp.level` (min **0**) | covered — with a real edge: a level-0 miner violates games-web's floor; the adapter clamps/offsets or games-web relaxes the minimum |
| `character.class` · `character.title` (req), `character.portrait` (opt) | none | serializer-constant — comic-RPG flavor with no producer truth needed |
| `stats[] {key,label,value}` (minItems 1) | `coins` · `energy.current`/60 · `depth` · `record_depth` · `position` · `vault_level` | covered-by-projection (labels/hints are serializer-side) |
| `gear{}` — 8 fixed fantasy slot keys, all required, `additionalProperties: false`, each slot **nullable** | `equipment` — closed 9-slot mining vocabulary | **semantically different**: 7/9 map injectively (helmet→head · chestplate→chest · leggings→legs · boots→feet · weapon→main_hand · shield→off_hand · charm→trinket); mineverse `tool` and `light` — the two mining-defining slots — have no home (only `hands` is free, and it is one slot for two); games-web `hands` has no mineverse source but degrades cleanly to `null` |
| `gear.<slot>.name` (req when slot non-null) | `equipment` values (open-ended item-name strings) | covered for the 7 mapped slots |
| `gear.<slot>.rarity` (req when slot non-null, enum common…legendary) | none — no rarity concept anywhere in the snapshot or the oracle item model it projects | **semantically different** — and NOT cheaply additive: the producer has no truth to project |
| `gear.<slot>.power` (opt) | none (`gear_wear` is a different semantic: accumulated wear, not power) | no source |
| *(reverse)* `gear_wear` countMap | — | games-web has NO wear field on `gearSlot`: the one gear datum mineverse renders beyond names is dropped |
| `skills[] {key,label,level,xp,xp_max}` | `skills` countMap name→rank | `key`/`level` covered, `label` serializer-side; `xp` · `xp_max` (both required) — **semantically different**: the snapshot's `xp` is the game-level quartet {game, game_total, shared_total, level}; nothing per-skill exists |
| `structures[] {key,label,tier,status}` | `structures` countMap name→count/tier | `key`/`tier` covered, `label` serializer-side; `status` (required enum idle·working·upgrading·locked) — **semantically different**: no producer truth |

## Headline

Every games-web field family is covered or projection-covered EXCEPT
three required leaves — `gear.<slot>.rarity`, `skills[].xp`/`xp_max`,
`structures[].status` — plus the gear-slot vocabulary (7/9 injective,
`tool`/`light` homeless), and **all three misses are games-web-side
presentation flavor with no producer truth behind them: there is NO
producer data debt in `mining_snapshot.v1`.** This audit re-ran the
idea-engine probe's first cut against both schemas and confirms its
findings, adding two first-hand edges the probe did not name (the
level-0 floor mismatch; the nullable-slot degradation for `hands`).

Costing consequence for seam option (A): one **client-side adapter**
(slot map + serializer constants for `class`/`title`/labels +
miner-selection + level clamp, with `rarity`/`status`/xp-bars degrading
gracefully) **plus one games-web patch bump** relaxing the three flavor
requireds to optional — **zero breaking changes to
`mining_snapshot.v1`**. Making the snapshot grow `rarity` or `status`
would invent data the oracle does not own; the cheap fix lives
consumer-side (that half belongs to product-forge, not this repo).

## Not measured (named, not invented)

- **Per-skill xp reachability** — whether superbot's `game_xp_service`
  tracks per-skill xp (the ONLY candidate additive v1 family this audit
  surfaces) is a superbot-repo question. Not answerable from either
  contract file; **not measured here**. If it is not tracked, games-web
  skill bars must degrade to level-only.
- **Pin freshness** — whether `a9c7401` is still product-forge HEAD, and
  whether games-web has since shipped a consumer (the event that closes
  the cheap-relaxation window). Not measured here.

## Durable gate

The importable constants this audit leans on (`REQUIRED_MINER_FIELDS`,
`REQUIRED_ENVELOPE_FIELDS`) now live in `snapshot_contract.py` (repo
root, schema-derived at import time — landed in the same PR as this
audit), so a future adapter and both CI gates can import one artifact
instead of re-deriving field lists. The slot map above is committed
prose; promoting it into `snapshot_contract.py` is deliberately deferred
until the seam ruling picks option (A) — a constant nobody imports yet
would be speculation, not contract.
