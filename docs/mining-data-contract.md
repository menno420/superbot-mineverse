# superbot-mineverse — mining snapshot READ contract (v1)

> **Status:** `binding`
>
> The versioned READ contract between the superbot bot side (producer) and
> this web app (consumer). Machine-checkable twin:
> `schemas/mining_snapshot.v1.schema.json` (JSON Schema draft 2020-12),
> enforced in CI by `tests/test_schema_gate.py` against the committed sample.
> Where prose and schema disagree, the schema wins for shape; this doc wins
> for semantics.

## Purpose

The bot owns the live mining state in Postgres. This web app never touches
that database and never holds the bot token — it is a **client only**. The
bot side projects live mining state into the part-4d bot→web **read relay**
as snapshot documents; the web app serves and renders whatever conformant
snapshot it was last given. In stage 1 the "relay" is a committed fixture
(`data/sample_snapshot.json`) served verbatim by `GET /api/snapshot`; the
contract below is what the real bot-side producer will eventually fulfil,
unchanged.

Strictly read-only: no auth, no database, no secrets anywhere in this repo.

## The snapshot envelope

A snapshot is a single JSON object:

| Field | Type | Required | Semantics |
|---|---|---|---|
| `schema_version` | string, exactly `"1"` | yes | Contract major version (see Versioning). |
| `generated_at` | string, ISO 8601 UTC (`format: date-time`, e.g. `2026-07-11T12:00:00Z`) | yes | The instant the bot projected this snapshot. Consumers derive staleness from it. |
| `guild_id` | string of digits | yes | Discord guild snowflake the snapshot is scoped to. **Snowflakes are strings on the wire**: they exceed IEEE-754 double precision, so a JSON number would be silently corrupted by JS consumers. |
| `miners` | array of miner objects | yes | One entry per `mining_player_state` row in the guild. May be empty. |
| `max_depth` | integer 0–3 | no | World-shape hint: deepest reachable depth index (oracle-confirmed bands 0–3). |
| `biomes` | array of strings, ≤ 4 entries | no | World-shape hint: biome display name per depth index (0 = Surface, 1 = Cavern, 2 = the Deep, 3 = the Magma core). |

The envelope is **closed** (`additionalProperties: false`): a producer field
the schema does not declare is a contract violation, not a soft extra. New
optional fields are added by updating the v1 schema file (see Versioning).
Consumers must render sensibly when the optional hints are absent (the
frontend carries biome/depth fallbacks).

## Per-miner fields (oracle field names)

Field names deliberately mirror the superbot oracle's `mining_player_state`
so the producer is a projection, not a translation layer. Sources: the
mining state lives per `(suid, guild_id)` and is mutated only through
`disbot/services/mining_workflow.py` (single-transaction ops); `coins` is
mutated only by `economy_service`; `xp` comes from `game_xp_service`.

| Field | Type | Required | Semantics | Oracle source |
|---|---|---|---|---|
| `suid` | string of digits | yes | Superbot user id (Discord user snowflake). | player-state key |
| `guild_id` | string of digits | yes | Guild snowflake; with `suid` forms the state key. Matches the envelope `guild_id` in v1. | player-state key |
| `display_name` | string | yes | Guild display name, resolved bot-side at projection time. | Discord member cache, bot-side |
| `depth` | integer 0–3 | yes | Current depth index (oracle-confirmed bands 0–3, 0 = surface). | `mining_workflow` / `mining_player_state` |
| `record_depth` | integer 0–3 | yes | Deepest depth ever reached. | `mining_workflow` / `mining_player_state` |
| `position` | object `{x: int, y: int, …}` | yes | Grid coordinates on the current depth. Open object: discovery/exploration fields may arrive additively. | `mining_workflow` / `mining_player_state` |
| `energy` | object `{current: int 0–60, updated_at: int ≥ 0, …}` | yes | Energy meter; oracle-confirmed cap is 60. `updated_at` is unix epoch seconds of the last recalculation. Open object. | `mining_workflow` / `mining_player_state` |
| `coins` | integer ≥ 0 | yes | Coin balance. | `economy_service` (sole coin mutator) |
| `xp` | object `{game: str, game_total: int ≥ 0, shared_total: int ≥ 0, level: int ≥ 0, …}` | yes | XP projection: per-game total, account-shared total, derived level. Open object. | `game_xp_service` |
| `equipment` | object, string values, slot keys from a closed enum | yes | Slot → equipped item name map. Oracle-confirmed slot set: `tool`, `light`, `charm`, `weapon`, `shield`, `helmet`, `chestplate`, `leggings`, `boots` (the schema enforces the key enum; item names stay open strings). | `mining_workflow` + `disbot/utils/equipment.py` |
| `gear_wear` | object, int ≥ 0 values | yes | Dynamic item name → accumulated wear map for equipped gear. | `mining_workflow` / `mining_player_state` |
| `mining_inventory` | object, int ≥ 0 values | yes | Dynamic item name → quantity map: carried underground. Ore progression runs stone → diamond, but keys stay open — the pack also holds non-ore items (wood, torch, ration, …). | `mining_workflow` / `mining_player_state` |
| `vault` | object, int ≥ 0 values | yes | Dynamic item name → quantity map: banked items (same open key space as `mining_inventory`). | `mining_workflow` / `mining_player_state` |
| `vault_level` | integer 0–6 | yes | Vault upgrade tier (oracle-confirmed range 0–6). | `mining_workflow` / `mining_player_state` |
| `skills` | object, int ≥ 0 values | yes | Dynamic skill name → rank map. | `mining_workflow` / `mining_player_state` |
| `structures` | object, int ≥ 0 values | yes | Dynamic structure name → count/tier map. | `mining_workflow` / `mining_player_state` |

The miner object itself is **closed** (`additionalProperties: false`); the
dynamic-key maps inside it (`mining_inventory`, `vault`, `equipment`,
`gear_wear`, `skills`, `structures`) are deliberately **open on keys** —
item/skill/structure/slot names are oracle-owned strings that change with
game content, so the schema constrains only their value types.

## Versioning policy

- `schema_version` is a **string**. v1 is exactly the string `"1"` — the
  schema pins it with `const: "1"` (a const, not a pattern; documented here
  as the chosen option).
- **Within v1, changes are additive-only**: new OPTIONAL envelope or miner
  fields (and new keys inside the dynamic maps, which are always free) are
  added by updating `mining_snapshot.v1.schema.json` in place. An additive
  change never bumps `schema_version`.
- **Any breaking change** — renaming or removing a field, changing a type,
  or changing a field's semantics — bumps to `"2"` and ships a **new**
  schema file (`schemas/mining_snapshot.v2.schema.json`); the v1 file is
  frozen at that point so old payloads stay checkable.
- Consumers must reject (or visibly flag) a snapshot whose `schema_version`
  they do not support, rather than guessing.

## Delivery expectations

- **Cadence**: the bot pushes a fresh snapshot into the read relay
  periodically — target every **60 s** — plus on-demand refreshes when the
  owner or a workflow requests one. The web app never pulls from the bot;
  it only reads the relay's latest document.
- **Staleness**: consumers compare `generated_at` to now. Beyond a staleness
  threshold (default suggestion: 3 missed cycles ≈ 180 s), the frontend
  shows a stale indicator next to the snapshot metadata instead of
  presenting old numbers as live. Stage 1 serves a committed fixture, so its
  `generated_at` is honest about being a fixture — permanently "stale" is
  the correct stage-1 reading.
- **Atomicity**: a snapshot is replaced whole, never patched; a reader never
  observes a half-written document.

## Enforcement

- `tests/test_schema_gate.py` validates `data/sample_snapshot.json` against
  the v1 schema with `jsonschema.Draft202012Validator` on every test run.
- **The schema is the single source of truth for required fields**:
  `tests/test_snapshot.py` derives its `REQUIRED_MINER_FIELDS` from the
  schema's per-miner `required` list instead of keeping a hand-copied
  constant, so the test and the schema cannot drift.
- CI: `.github/workflows/schema-gate.yml` runs the full pytest suite (and
  with it the schema gate) on every PR and push to main. Dev-only pins live
  in `requirements-dev.txt` — the runtime backend stays stdlib-only.
