# Minigame section spec — SuperBot 2.0 (ORDER 004 item 4)

> **Status:** `plan`
>
> Section spec for the SuperBot 2.0 minigame/casino section: full cross-repo
> game inventory, the repos' OWN grouping, enable-all-or-pick semantics
> grounded in mechanisms that exist today, a dynamic-panel model, and a
> per-game readiness table. Design-level only — no code here. Audience: the
> SuperBot 2.0 lane that will build the panels.

## 1. Purpose + provenance

ORDER 004 item 4 (`control/inbox.md`, claim `control/claims/minigame-section-spec.md`
merged via PR #56) asked for a section spec covering every card/minigame
across the fleet. Everything below is drawn from four read-only inventories
pinned at these SHAs — re-verify against each repo's HEAD before building:

| Repo | Pinned SHA | Note |
|---|---|---|
| `menno420/superbot-next` | `7330bc1` | PR **#313** (fishing slice 1: forecast/sail + `fishing_venue` store) merged into origin/main 2026-07-13T00:48Z, **post-HEAD** (its base was exactly `7330bc1`) — post-HEAD deltas flagged inline |
| `menno420/superbot-games` | `64b3371` | zero open PRs at inventory time |
| `menno420/superbot-idle` | `457407c` | PRs #75 (PLUG-001 adapter) and #76 (theme wave 4) open |
| `menno420/superbot-mineverse` | `18f1fb3` | this repo; origin/main has since advanced (control-only commits) |

Recommendations in §3 are **proposals** for the owner/lane to ratify; sim and
balance questions (e.g. idle SIM-001 economy tuning) are explicitly out of
scope here.

## 2. Full inventory + game groups

Grouping below is the repos' OWN grouping, not an invention of this spec.

### 2.1 superbot-next — in-tree games (the hub roster)

The `!games`/`/games` hub renders two sections (`sb/domain/games/panels.py@7330bc1:104-148`):

- **🏆 Competitive** — blackjack, casino/poker, deathmatch, RPS/tournaments
  (`GAMES_COMPETITIVE`). Cross-game tournament state is one `guild_settings`
  KV row `active_tournament` written only by K7 tournament legs
  (`sb/domain/games/tournament_flag.py@7330bc1`).
- **🎲 Activities** — mining, fishing, creature, farm, counting, chain
  (`GAMES_ACTIVITIES`).
- **World hub** — `!world` Explore hub (⛏️ Mine / 🎣 Fish / 🐔 Farm primary
  buttons + Deathmatch/Casino/Creatures navs) and `!worldcard`/`!mystats`
  cross-game identity card (`games.world`, `games.world_card`).
- **BTD6** — its own help category ("BTD6 Assistant", 🐵, hub `!btd6`), NOT a
  games-hub entry (`sb/domain/help/categories.py@7330bc1:54-99`).
- **four_twenty** — easter-egg family (`!420` + passive per-message stage),
  not in the games hub (`sb/manifest/four_twenty.py@7330bc1`).
- **hello** — the working plugin exemplar
  (`examples/superbot-plugin-hello/`), proving the out-of-tree game seam.

### 2.2 superbot-games — pure-domain lanes (arrive via the game-plugin contract)

Four game lanes + one shared substrate, all pure-domain/stdlib/sim-only, no
live adapter anywhere in the repo (`docs/architecture.md@64b3371`):
**exploration** (quest engine + survival sim), **mining** (20-module core,
oracle port), **fishing** (catch skeleton + biomes), **D&D** (bounded-menu
story substrate), plus `games/shared/` (encounter seam, inventory contract,
economy sim). These reach SuperBot 2.0 only via superbot-next's binding
game-plugin contract (`docs/game-plugin-contract.md`, D-0056/ORDER 002:
plugin repo pinned in `plugins.lock.json`, loaded by `sb/app/plugin_host.py`;
parity goldens & migrations host-owned, refused by `plugin_gate`).

### 2.3 superbot-idle — engine + theme catalog

One deterministic, integer-exact idle engine (tick/offline/upgrades/prestige/
milestones/save-format-v2/setup-codes/render — `idle_engine/*@457407c`) skinned
by **12 data-only theme packs** on main (15 pending PR #76); mechanics
identical across the catalog by design (`themes/README.md@457407c`: "No code,
no new mechanics, ever"; gate-green = safe to enable unreviewed). The live
seam is the PLUG-001 adapter — open **PR #75** exporting
`SubsystemManifest(key="idle", …)` with one `idle` command → `idle.status`
PanelSpec, `capabilities=("idle",)`.

### 2.4 superbot-mineverse — web game (link-out panel candidate)

Read-mostly "mining guild viewer" web game over superbot's mining economy
(depth/biome ladder, leaderboards, miner cards, achievements, cosmetic
hats/seasonal/audio), stdlib backend, degraded-by-default env tiers 0–3
(`docs/current-state.md@18f1fb3`). Not a Discord-command game — its section
presence is a **link-out panel** (§4).

## 3. Enable-all-or-pick semantics

Grounded in mechanisms that EXIST today — there is **no per-game on/off flag
in any game manifest** (grep across `sb/manifest/*.py@7330bc1` finds none).
The layers, in resolve order:

| Layer | Mechanism (exists today) | Granularity |
|---|---|---|
| Guild-wide coarse switch | `!setup` channel-access modes — `CommandAccessSnapshot` `None \| ALL_CHANNELS \| SELECTED_CHANNELS \| DISABLED_EXCEPT_BOOTSTRAP` + per-channel role sets (`sb/kernel/authority/channel_access.py@7330bc1:118-135`) | guild / channel |
| **Per-game pick** | rows in `capability_execution_overrides` (migration `0016_governance.sql`) flip a capability allow/deny per guild — TTL-cached 600 s, **fail-closed** on unknown capability, no privilege escalation via guild rows (`sb/domain/governance/execution.py@7330bc1:1-38`). Every game command carries a capability group (`capability="blackjack"`, `"casino"`, `"mining"`, …) | guild × capability |
| Per-setting tunables | `SettingSpec` `Activation` enum (`sb/spec/settings.py@7330bc1:63-70`) — entry fees, timeouts; NOT enable bits | setting |
| Per-channel opt-in (message games) | chain via `chain_channels` rows (`!chain create`), counting via its channel state; per-message rules fire only where configured and only when the live adapter's MESSAGE FEED is armed | channel |
| Idle provisioning | FROZEN `IDLE1-` setup codes: `SetupConfig(theme_id, offline_progress, upgrades, prestige)`, CRC-16, fail-loud (`idle_engine/provisioning.py@457407c`, `docs/provisioning.md@457407c`) | guild (theme + feature flags) |
| Plugin enablement | pinning in `plugins.lock.json` via `tools/plugin_pin.py` (`docs/game-plugin-contract.md@7330bc1` §2) | deployment |
| Mineverse | env-var tiers 0–3 (tier 0 read-only anonymous → tier 3 owner-ORDER live-prod), `docs/current-state.md@18f1fb3` §Degraded by default | host env + owner ORDER |

**Specified semantics for the section:**

- **Section-level "enable all"** = batch-writing `capability_execution_overrides`
  allow rows for every capability in a group (e.g. all of 🏆 Competitive) in
  one admin action. No new mechanism — a batch write over the existing rows.
- **Per-game pick** = an individual `capability_execution_overrides` row.
- Message games (counting, chain) additionally keep their per-channel opt-in;
  the capability row is the section-level gate ABOVE that.
- Idle keeps the setup-code flow as its per-guild config surface; the `idle`
  capability row is the section-level gate.

**Recommended defaults (PROPOSAL — owner/lane to ratify; sim/balance
uncertainty out of scope):** 🏆 Competitive and 🎲 Activities **on** by
default; **BTD6 off** by default (its AI lane is owner-gated: `AI_ENABLED`
opt-in + `ANTHROPIC_API_KEY`, fail-closed — `sb/kernel/ai/flags.py@7330bc1:11-15`,
⚑ needs-owner #4); anything owner-gated (idle until PR #75 lands + pin,
games-repo lanes until host adapters exist, mineverse write tiers) **off**
until its gate clears.

## 4. Dynamic panels

Design-level model — no code in this section:

- Panels render from `SubsystemManifest`/`PanelSpec` data;
  `manifest.snapshot.json@7330bc1` is the hash-pinned compile of all
  subsystems (commands/panels/settings/stores/events/capabilities/wizard
  sections per subsystem).
- The games-hub roster in `sb/domain/games/panels.py@7330bc1` (two-section
  hub + world hub) is the **seed** for the section's panel layout.
- Panels should **hide or badge** games whose capability is disabled for the
  guild (a `capability_execution_overrides` deny/absent row) or whose
  readiness gates are still open (§5 owner-gate column) — e.g. BTD6's AI
  answers render shipped empty states until providers are armed (D-0046).
- Idle contributes its own `idle.status` PanelSpec via the PLUG-001 plugin
  seam (PR #75) — the section consumes it like any in-tree panel once the
  plugin is pinned.
- Mineverse is a **web link-out panel** (degraded-by-default: fully demoable
  at tier 0 on committed sample data) — a URL card, not a command surface.
- Games-repo lanes get panels only after their host adapters exist; until
  then they have no runtime surface to render.

## 5. Per-game READINESS table

One row per game across all four repos. "Goldens" = golden/vector corpus as
each repo defines it. Filled strictly from the pinned inventories; "not
verified" is stated where the inventories say so.

| Game | Repo | Group | Feature-complete? | Goldens | Live-adapter | Owner gates | Evidence |
|---|---|---|---|---|---|---|---|
| games (hub + substrate) | superbot-next | hub / band-6 substrate | yes — hub, `!world`, `!worldcard`, `g1:` sessions, checkpoint/XP stores | 4 | generic live pipeline; `g1:` dispatcher on component adapter | none found | `sb/manifest/games.py@7330bc1`; `parity/parity.yml@7330bc1:167-217` |
| blackjack | superbot-next | 🏆 Competitive | yes — solo, PvP, tournament orchestration | 7 | generic live dispatch + g1; D1 escrow via K7 | none (entry-fee setting is admin-floor) | `sb/domain/blackjack/*@7330bc1`; `sb/manifest/blackjack.py:21` |
| casino / poker | superbot-next | 🏆 Competitive | partial→near-complete — full in-hand engine; ephemeral per-player hands replaced by public spectator projection (ledgered deviation D-0045) | 3 | headless play layer; live per-player ephemeral hands = named D-0045 successor | none found | `sb/domain/casino/game.py@7330bc1` docstring; `docs/decisions.md@7330bc1:343` |
| RPS (`rps_tournament`) | superbot-next | 🏆 Competitive | yes — 7 commands, quick-play/PvP/tournament | 8 | generic live pipeline | none (defaults are settings) | `sb/domain/rps/*@7330bc1`; `sb/manifest/rps_tournament.py:35-48` |
| deathmatch | superbot-next | 🏆 Competitive | yes, one live-only gap — turn-timeout enforcement is the live adapter's obligation, **not verified implemented** | 2 | timeout enforcement live-adapter-only; else generic | `deathmatch_turn_timeout` setting | `sb/domain/deathmatch/*@7330bc1`; `docs/decisions.md@7330bc1:343`; `sb/manifest/deathmatch.py:23` |
| mining / deep-mining | superbot-next | 🎲 Activities | partial (deep) — all 26 deep-system commands routed live (D-0043 ladder complete); deferred: argful `!cook`/`!use`, structure BUILD write, skill/title writes | **42** | generic live; write-parity in flight | dig-gating `!fastmine` **awaits OWNER DECISION** (PR #320 body); open PRs **#312/#317/#320** | `sb/domain/mining/service.py@7330bc1:957-993`; ladder PRs #286→#300 |
| fishing | superbot-next | 🎲 Activities | partial — core cast loop live at starter profile; **15 pending commands** at HEAD; **PR #313 merged post-HEAD** (forecast/sail + `fishing_venue`, goldens 7→9) | 5 (+15 sweeps parked in `goldens/_unmapped/`) | generic live pipeline | was owner-gated on D-0043 go/no-go (⚑ #1, `control/status.md@7330bc1`) — answered post-HEAD via #313 | `sb/domain/fishing/service.py@7330bc1:167-183` |
| creature | superbot-next | 🎲 Activities | partial (high) — catch/dex complete; battle engine landed (D-0079); pending: trainer-picker/Rematch seam | 10 | generic live; battle seeded for replay | none found | `docs/decisions.md@7330bc1:587-589`; `sb/domain/creature/*` |
| farm | superbot-next | 🎲 Activities | yes — "FARM (complete)" per D-0043 | 1 | generic live pipeline | none found | `docs/decisions.md@7330bc1:329`; `sb/domain/farm/*` |
| counting | superbot-next | 🎲 Activities (message game) | yes — 10-command surface + on-message lane | 10 | per-message rule arms with live MESSAGE FEED | none found | `sb/manifest/counting.py@7330bc1` docstring |
| chain | superbot-next | 🎲 Activities (message game) | yes — `!chain` group + `!chainmenu` | 7 | MESSAGE FEED | none; per-channel via `chain_channels` | `sb/manifest/chain.py@7330bc1` docstring |
| four_twenty | superbot-next | easter egg (not in hub) | yes | 1 | MESSAGE FEED (passive tier) | none found | `sb/manifest/four_twenty.py@7330bc1` |
| btd6 | superbot-next | own category (band 7) | partial — 39 command shapes pinned; live NK ingestion = D-0046 successor (empty states shipped) | **104** | generic live; AI answers need providers armed | **AI gate**: `AI_ENABLED` + `ANTHROPIC_API_KEY` (⚑ needs-owner #4); fails closed | `sb/manifest/btd6.py@7330bc1`; `sb/kernel/ai/flags.py@7330bc1:11-15` |
| hello (plugin exemplar) | superbot-next | plugin seam | stub/exemplar — headless boot proven in CI; live `/hello` = human runbook | none (plugins excluded from parity, contract §2) | install dist → boot → slash-sync runbook | plugin repo creation is owner-side | `examples/superbot-plugin-hello/`; `docs/game-plugin-contract.md@7330bc1` |
| exploration | superbot-games | pure-domain lane | P1 quest engine complete for v1 scope + P2 survival sim; **not playable** (no host adapter, no AI-DM, hub/map deferred per Q-0182) | sim-pinned (no JSON golden); 55/55 tests | **none — sim-only** | host-adapter rung owner-⚑ | `docs/current-state.md@64b3371`; PRs #3/#32 |
| mining | superbot-games | pure-domain lane | core port substantially complete vs oracle; not playable (no workflow/host layers) | **5,760-record encounter golden**; 96/88 tests | **none** — rung 2 parked owner-⚑ (PR #60), rung 3 blocked owner-⚑ packaging (PR #66) | owner ⚑ ×2 (workflow ratification; packaging/hermeticity) | `games/mining/core/*@64b3371`; `tests/mining/_encounter_golden.json@64b3371` |
| fishing | superbot-games | pure-domain lane | skeleton-stage by its own design doc (catch loop + biomes + inventory adapter) | sim-pinned; 64/64 tests | **none — sim-only** | host-adapter owner-⚑ | `docs/design/fishing-catch-skeleton.md@64b3371`; PRs #25/#33/#35 |
| D&D | superbot-games | pure-domain lane | walking skeleton + first content slices; explicitly not a full story game; AI-DM layer does not exist | fuzz/sim-pinned; 31/31 tests | **none — sim-only** | host-adapter owner-⚑ | `games/dnd/*@64b3371`; PRs #48/#50/#52 |
| idle (engine + 12 theme packs) | superbot-idle | plugin lane (PLUG-001) | engine complete (tick/offline/upgrades/prestige/milestones/saves/setup-codes/render); economy numbers PROVISIONAL, tuning blocked on SIM-001; generator purchase not built | setup-code vectors (60+73+25) + save vectors (7+6+32); **1131 tests passed locally** (`python3 -m pytest -q` at `457407c`: `1131 passed in 14.50s`) | **adapter = open PR #75** (thin `SubsystemManifest`, `idle.status` PanelSpec); on main: no adapter, no bot runtime | auto-merge enabler inert until owner UI settings; SIM-001 verdict pending; 15-pack wave = open PR #76 | `idle_engine/*@457407c`; `tests/vectors/*@457407c`; PR #75 head `712e162` |
| mineverse (web game) | superbot-mineverse | link-out panel | read side complete (tier 0 fully demoable on sample data); write UI degraded by default; live data + real writes externally pending | none (served-bytes pin tests instead); **437 passed, 1 skipped in 66.22s** at `18f1fb3` | web link-out; bot-side FLAG 1 (READ relay) + FLAG 2 (WRITE endpoint) externally pending; no relay-ingestion path exists yet | **FLAG 1/2** + `MINING_WRITE_ENDPOINT`/`MINING_WRITE_SHARED_SECRET` env pair + stage-(d) owner ORDER | `docs/current-state.md@18f1fb3`; `server/snapshot_validation.py`; `control/status.md@18f1fb3` |

Substrate rows (not games, bind the above): superbot-games `games/shared/`
(encounter seam, inventory contract, economy sim → `docs/balance.md`
CI-freshness, 64/64 tests) and superbot-next non-game neighbours (treasury,
economy, counters, karma/xp) are out of the section.

**Readiness headline:** 20 game rows; 10 in-tree superbot-next games ride the
generic live pipeline today (blackjack, RPS, deathmatch, farm, counting,
chain, four_twenty fully; games-hub, mining, creature, fishing, casino, btd6
partial); 4 games-repo lanes are sim-only with zero live adapters
(owner-⚑ on the host-adapter rung); idle is one open PR (#75) from its live
seam; mineverse is web-only, live data owner/externally gated.

## 6. Honest nulls / unverified

Carried over verbatim from the inventories — do not treat as settled:

- **deathmatch** live turn-timeout enforcement: named the live adapter's
  obligation; no implementation observed — not verified.
- **creature** trainer-picker/Rematch in-flight work: none found at HEAD —
  not verified anywhere.
- **Oracle-completeness of ports not diffed**: superbot-games mining/fishing
  ports were not diffed against `menno420/superbot`; superbot-next parity is
  gate-attested, not re-derived here.
- **superbot-next PR #277/#302 contents** taken from PR #313's provenance
  text, not independently read.
- **superbot-next games band live-drive has not run** (testing ladder row 8
  "pending", `docs/status/testing-report-2026-07-09.md@7330bc1`); live-drive
  is human-operator-only (no gateway token in CI).
- **Branch-protection-required state of idle checks** (`pytest`,
  `theme-gate`): unverified; workflow comments say no required checks existed
  at 2026-07-12 install time.
- **Idle PR #75/#76 suite claims** (1131+skips under host / 1227 at 15
  packs): not run locally — only main@`457407c` was tested (1131 passed).
- **Idle SIM-001** economy verdict: still awaiting relay (null).
- **game-plugin-contract content at `d3dba9b`** cited via idle's own probe
  log (`docs/plugin-adapter-scoping.md@457407c`), not independently fetched
  by the idle inventory.
- **Mineverse relay ingestion**: only snapshot source is the committed
  `data/sample_snapshot.json`; no relay-ingestion endpoint/path exists yet.
