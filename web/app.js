/* Mineverse frontend — renders the deepened read views from /api/views
 * (server/views.py shapes the snapshot server-side so pytest covers every
 * render path; this file only paints). Field names mirror superbot's
 * mining_player_state (mining_inventory, depth, position, equipment,
 * gear_wear, vault, vault_level, energy, coins, skills, structures) +
 * game_xp_service (xp). */

"use strict";

// Contract-documented biome display names (docs/mining-data-contract.md):
// consumers carry fallbacks for when the optional world-shape hints are
// absent. The ladder gets honest server-side "depth N" labels instead.
const FALLBACK_BIOMES = ["Surface", "Cavern", "the Deep", "the Magma core"];
const BIOME_ICONS = ["🌳", "🪨", "💎", "🌋"];

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function showBanner(message, isError) {
  const banner = document.getElementById("status-banner");
  banner.textContent = message;
  banner.classList.toggle("error", Boolean(isError));
  banner.hidden = false;
}

function biomeLabel(depth, biomes) {
  const names = Array.isArray(biomes) && biomes.length ? biomes : FALLBACK_BIOMES;
  const idx = Math.max(0, Math.min(depth, names.length - 1));
  return `${BIOME_ICONS[idx] || ""} ${names[idx]}`.trim();
}

/* --- snapshot staleness (header) ----------------------------------------- */

function formatAge(seconds) {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`;
  return `${Math.floor(seconds / 86400)}d`;
}

function renderStaleness(staleness) {
  // Age is computed HERE, against the browser clock, once per page load —
  // no live ticking. The server only ships generated_at (+ its epoch) and
  // the contract-prose thresholds (60 s cadence, stale beyond ~180 s —
  // docs/mining-data-contract.md § Delivery expectations).
  const line = document.getElementById("snapshot-staleness");
  line.hidden = false;
  line.classList.remove("fresh", "warn", "stale");
  const epoch = staleness?.generated_at_epoch;
  if (typeof epoch !== "number") {
    line.classList.add("warn");
    line.textContent =
      "⚠ snapshot age unknown — generated_at is missing or unreadable";
    return;
  }
  const age = Math.floor(Date.now() / 1000) - epoch;
  const threshold = staleness?.stale_after_seconds ?? 180;
  const cadence = staleness?.cadence_seconds ?? 60;
  if (age < 0) {
    line.classList.add("warn");
    line.textContent =
      `⚠ snapshot timestamped ${formatAge(-age)} in the future — check clocks`;
  } else if (age >= threshold) {
    line.classList.add("stale");
    line.textContent =
      `⚠ STALE — snapshot ${formatAge(age)} old, expected every ` +
      `${cadence}s (age as of page load)`;
  } else {
    line.classList.add("fresh");
    line.textContent = `snapshot ${formatAge(age)} old (age as of page load)`;
  }
}

/* --- miner cards (gear / pack / vault panels, shaped server-side) ------- */

function groupedItemList(group) {
  // group = {ores: [[name, qty]...], other: [[name, qty]...]} — ore tiers
  // stone→diamond first (server-ordered), then the rest alphabetically.
  const entries = [...(group?.ores || []), ...(group?.other || [])];
  if (!entries.length) return [el("p", "empty", "(empty)")];
  const oreCount = (group?.ores || []).length;
  const ul = el("ul", "items");
  entries.forEach(([name, qty], i) => {
    ul.appendChild(el("li", i < oreCount ? "ore" : null, `${qty}× ${name}`));
  });
  return [ul];
}

function gearList(gear) {
  // gear = [{slot, item|null, wear|null}] — every schema slot, always.
  if (!Array.isArray(gear) || !gear.length) {
    return [el("p", "empty", "(no gear data)")];
  }
  const ul = el("ul", "items gear-list");
  for (const { slot, item, wear } of gear) {
    const li = el("li", item ? null : "slot-empty");
    li.appendChild(el("span", "slot-name", slot));
    li.appendChild(el("span", null, item
      ? ` ${item}${wear !== null && wear !== undefined ? ` · wear ${wear}` : ""}`
      : " — empty"));
    ul.appendChild(li);
  }
  return [ul];
}

function rankedList(pairs, format) {
  // pairs = [[name, value]...] — highest value first (server-ordered);
  // skill/structure names are contract-open, so everything renders as-is.
  if (!Array.isArray(pairs) || !pairs.length) {
    return [el("p", "empty", "(none)")];
  }
  const ul = el("ul", "items");
  for (const [name, value] of pairs) {
    ul.appendChild(el("li", null, format(name, value)));
  }
  return [ul];
}

function formatEpochUTC(epoch) {
  // Unix epoch seconds -> "2026-07-11 12:00 UTC" — snapshot data,
  // rendered verbatim, never ticked forward.
  return `${new Date(epoch * 1000).toISOString().slice(0, 16).replace("T", " ")} UTC`;
}

function energyMeter(energy) {
  // energy = {current, updated_at, max} — schema-shaped server-side
  // (max is the contract's 0–60 bound). Strictly "as of" presentation:
  // no regen simulation, no live ticking.
  const row = el("div", "energy-row");
  const current = energy?.current;
  const max = energy?.max;
  row.appendChild(el("span", "energy-label", `⚡ ${current ?? "?"}/${max ?? "?"}`));
  const track = el("div", "energy-track");
  const bar = el("div", "energy-bar");
  const known = typeof current === "number" && typeof max === "number" && max > 0;
  bar.style.width = known
    ? `${Math.max(0, Math.min(current / max, 1)) * 100}%`
    : "0%";
  if (known && current / max <= 0.2) bar.classList.add("low");
  track.appendChild(bar);
  row.appendChild(track);
  row.appendChild(el("span", "energy-asof",
    typeof energy?.updated_at === "number"
      ? `as of ${formatEpochUTC(energy.updated_at)}`
      : "as of snapshot (update time unknown)"));
  return row;
}

function vaultTierPips(level, levelMax) {
  const filled = "●".repeat(Math.max(0, Math.min(level, levelMax)));
  const hollow = "○".repeat(Math.max(0, levelMax - level));
  return `${filled}${hollow}`;
}

function section(card, title, nodes) {
  card.appendChild(el("h4", null, title));
  nodes.forEach((n) => card.appendChild(n));
}

function renderMinerCard(miner, world) {
  const card = el("article", "card");
  card.appendChild(el("h3", null, miner.display_name));
  card.appendChild(
    el("p", "depth-line",
      `Depth ${miner.depth}/${world.max_depth} — ` +
      `${biomeLabel(miner.depth, world.biomes)}` +
      (miner.position ? ` · at (${miner.position.x}, ${miner.position.y})` : "") +
      ` · record depth ${miner.record_depth}`),
  );
  const xp = miner.xp || {};
  card.appendChild(
    el("p", "xp-line",
      `Level ${xp.level ?? "?"} · ${xp.game_total ?? 0} mining XP · ` +
      `${miner.coins ?? 0} 🪙`),
  );
  card.appendChild(energyMeter(miner.energy));
  section(card, "Gear", gearList(miner.gear));
  section(card, "Pack", groupedItemList(miner.pack));
  section(card, "Skills",
    rankedList(miner.skills, (name, rank) => `${name} · rank ${rank}`));
  section(card, "Structures",
    rankedList(miner.structures, (name, count) => `${count}× ${name}`));
  const vault = miner.vault || {};
  const vaultTitle = el("h4", null, `Vault · level ${vault.level ?? 0} `);
  vaultTitle.appendChild(
    el("span", "vault-pips", vaultTierPips(vault.level ?? 0, vault.level_max ?? 0)));
  card.appendChild(vaultTitle);
  groupedItemList(vault).forEach((n) => card.appendChild(n));
  return card;
}

/* --- depth race (relative bar view, kept alongside the ladder) ---------- */

function renderDepthRace(miners, world) {
  const race = document.getElementById("depth-race");
  race.replaceChildren();
  for (const miner of [...miners].sort((a, b) => b.depth - a.depth)) {
    const row = el("div", "race-row");
    row.appendChild(el("span", "race-name", miner.display_name));
    const track = el("div", "race-track");
    const bar = el("div", "race-bar");
    bar.style.width =
      `${world.max_depth ? (miner.depth / world.max_depth) * 100 : 0}%`;
    track.appendChild(bar);
    row.appendChild(track);
    row.appendChild(el("span", "race-depth", biomeLabel(miner.depth, world.biomes)));
    race.appendChild(row);
  }
}

/* --- depth/biome ladder (bands 0–3, current + record markers) ----------- */

function renderLadder(ladder) {
  const holder = document.getElementById("depth-ladder");
  holder.replaceChildren();
  for (const band of ladder || []) {
    const row = el("div", "ladder-band");
    const label = el("div", "ladder-label");
    label.appendChild(el("span", "ladder-biome",
      `${BIOME_ICONS[band.depth] || ""} ${band.biome}`.trim()));
    label.appendChild(el("span", "ladder-depth", `depth ${band.depth}`));
    row.appendChild(label);
    const chips = el("div", "ladder-chips");
    for (const name of band.here) {
      chips.appendChild(el("span", "chip", name));
    }
    for (const name of band.record_only) {
      chips.appendChild(el("span", "chip record", `${name} · record`));
    }
    if (!band.here.length && !band.record_only.length) {
      chips.appendChild(el("span", "empty", "(nobody here)"));
    }
    row.appendChild(chips);
    holder.appendChild(row);
  }
}

/* --- position mini-map (per depth band, server-shaped points) ------------ */

const MINIMAP_PAD = 1; // plot margin, in grid cells, around the outer points

function minimapPlot(panel) {
  // panel.bounds is the integer envelope of the band's points; each point
  // lands proportionally inside it (padded so nobody sits on the border).
  const plot = el("div", "minimap-plot");
  const spanX = (panel.bounds.max_x - panel.bounds.min_x) + 2 * MINIMAP_PAD;
  const spanY = (panel.bounds.max_y - panel.bounds.min_y) + 2 * MINIMAP_PAD;
  for (const point of panel.points) {
    const dot = el("span", "minimap-point");
    dot.style.left =
      `${(((point.x - panel.bounds.min_x) + MINIMAP_PAD) / spanX) * 100}%`;
    dot.style.top =
      `${(((point.y - panel.bounds.min_y) + MINIMAP_PAD) / spanY) * 100}%`;
    dot.title = `${point.name} at (${point.x}, ${point.y})`;
    dot.appendChild(
      el("span", "minimap-name", `${point.name} (${point.x}, ${point.y})`));
    plot.appendChild(dot);
  }
  return plot;
}

function renderMinimap(minimap) {
  const holder = document.getElementById("minimap");
  holder.replaceChildren();
  for (const panel of minimap || []) {
    const points = panel.points || [];
    const unplotted = panel.unplotted || [];
    if (!points.length && !unplotted.length) continue; // empty band: skip
    const band = el("div", "minimap-band");
    const label = el("div", "ladder-label");
    label.appendChild(el("span", "ladder-biome",
      `${BIOME_ICONS[panel.depth] || ""} ${panel.biome}`.trim()));
    label.appendChild(el("span", "ladder-depth", `depth ${panel.depth}`));
    band.appendChild(label);
    const body = el("div", "minimap-body");
    if (panel.bounds) {
      body.appendChild(minimapPlot(panel));
    } else {
      body.appendChild(el("p", "empty", "(no plottable positions here)"));
    }
    for (const name of unplotted) {
      body.appendChild(el("p", "empty", `${name} — position unknown`));
    }
    band.appendChild(body);
    holder.appendChild(band);
  }
  if (!holder.children.length) {
    holder.appendChild(el("p", "empty", "(no miner positions to plot)"));
  }
}

/* --- leaderboards (tabbed: depth · XP level · coins) --------------------- */

const BOARD_TABS = [
  ["depth", "Depth"],
  ["xp_level", "XP level"],
  ["coins", "Coins"],
];

function renderBoard(board) {
  const table = document.getElementById("leaderboard");
  const thead = table.querySelector("thead");
  const tbody = table.querySelector("tbody");
  thead.replaceChildren();
  tbody.replaceChildren();
  const headRow = el("tr");
  ["#", "Miner", ...(board?.columns || [])]
    .forEach((c) => headRow.appendChild(el("th", null, c)));
  thead.appendChild(headRow);
  for (const row of board?.rows || []) {
    const tr = el("tr");
    row.forEach((cell) => tr.appendChild(el("td", null, String(cell))));
    tbody.appendChild(tr);
  }
}

function renderBoardTabs(leaderboards) {
  const tabs = document.getElementById("board-tabs");
  tabs.replaceChildren();
  let active = BOARD_TABS[0][0];
  const buttons = new Map();
  const select = (key) => {
    active = key;
    for (const [k, b] of buttons) b.classList.toggle("active", k === active);
    renderBoard(leaderboards?.[active]);
  };
  for (const [key, label] of BOARD_TABS) {
    const button = el("button", "board-tab", label);
    button.type = "button";
    button.addEventListener("click", () => select(key));
    buttons.set(key, button);
    tabs.appendChild(button);
  }
  select(active);
}

/* --- inventory browser (guild matrix: item × miner, ores first) --------- */

function renderInventory(matrix) {
  const holder = document.getElementById("inventory-browser");
  holder.replaceChildren();
  if (!matrix || !matrix.rows || !matrix.rows.length) {
    holder.appendChild(el("p", "empty", "(no items carried by anyone)"));
    return;
  }
  const table = el("table", "inventory-table");
  const thead = el("thead");
  const headRow = el("tr");
  ["Item", "Total", ...matrix.columns]
    .forEach((c) => headRow.appendChild(el("th", null, c)));
  thead.appendChild(headRow);
  table.appendChild(thead);
  const tbody = el("tbody");
  for (const row of matrix.rows) {
    const tr = el("tr");
    row.forEach((cell, i) => {
      const td = el("td", null, i >= 2 && cell === 0 ? "·" : String(cell));
      if (i === 0) td.className = "item-name";
      if (i === 1) td.className = "item-total";
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  }
  table.appendChild(tbody);
  holder.appendChild(table);
}

/* --- top-level render ------------------------------------------------------ */

function render(views) {
  // /api/views is the snapshot (READ contract v1) shaped server-side —
  // schema_version/generated_at pass through for the meta line.
  const meta = document.getElementById("snapshot-meta");
  meta.textContent =
    `snapshot v${views.schema_version ?? "?"} · ` +
    `generated ${views.generated_at || "unknown"}`;
  renderStaleness(views.staleness);

  const miners = views.miners || [];
  if (!miners.length) {
    showBanner("Snapshot loaded, but it contains no miners.", false);
    return;
  }

  renderLadder(views.ladder);
  renderDepthRace(miners, views.world);
  renderMinimap(views.minimap);
  renderBoardTabs(views.leaderboards);
  renderInventory(views.inventory);
  const cards = document.getElementById("miner-cards");
  cards.replaceChildren();
  miners.forEach((m) => cards.appendChild(renderMinerCard(m, views.world)));

  for (const id of ["depth-ladder-section", "depth-race-section",
                    "minimap-section", "leaderboard-section",
                    "inventory-browser-section", "miners-section"]) {
    document.getElementById(id).hidden = false;
  }
}

/* --- Discord sign-in (stage b): /api/me drives the personal view. ------- */

function renderAuthControls(me) {
  const box = document.getElementById("auth-controls");
  box.replaceChildren();
  if (!me) return; // /api/me unreachable — public views stand on their own
  if (me.signed_in) {
    box.appendChild(el("span", "auth-user", `Signed in as ${me.user_id}`));
    const signOut = el("a", "auth-button", "Sign out");
    signOut.href = "/auth/logout";
    box.appendChild(signOut);
  } else if (me.auth_configured === false) {
    const disabled = el("button", "auth-button", "sign-in not configured");
    disabled.disabled = true;
    disabled.title =
      "The host has not provided Discord OAuth credentials — public views still work.";
    box.appendChild(disabled);
  } else {
    const signIn = el("a", "auth-button", "Sign in with Discord");
    signIn.href = "/auth/login";
    box.appendChild(signIn);
  }
}

function renderMyMiner(me, views) {
  if (!me || !me.signed_in) return;
  const section = document.getElementById("my-miner-section");
  const note = document.getElementById("my-miner-note");
  const holder = document.getElementById("my-miner-card");
  section.hidden = false;
  // /api/me returns the raw miner; the shaped twin (gear/pack/vault
  // panels) comes from /api/views by suid — same snapshot file underneath.
  const shaped = me.miner
    ? (views?.miners || []).find((m) => m.suid === me.miner.suid)
    : null;
  if (shaped) {
    holder.replaceChildren(renderMinerCard(shaped, views.world));
  } else if (me.miner) {
    note.textContent =
      `Signed in as ${me.user_id} — miner found, but the views service ` +
      "is unavailable, so the detailed card cannot render.";
    note.hidden = false;
  } else {
    note.textContent =
      `Signed in as ${me.user_id} — no miner found in this snapshot.`;
    note.hidden = false;
  }
}

/* --- Write actions (stage c): PROPOSALS to the bot, test economy only. ---
 * docs/mining-write-contract.md. The browser only ever sends
 * {action_id, action, params} to POST /api/action on THIS server; the
 * server derives suid from the session cookie, attaches guild_id, and
 * signs with a secret the browser never sees. Degraded by default:
 * without MINING_WRITE_ENDPOINT/MINING_WRITE_SHARED_SECRET on the host,
 * buttons render disabled and nothing else changes. */

const DISABLED_TOOLTIP = "Writes not configured — read-only mode";

function newActionId() {
  if (window.crypto && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  // Fallback UUIDv4 for older browsers.
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = [...bytes].map((b) => b.toString(16).padStart(2, "0")).join("");
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-` +
         `${hex.slice(16, 20)}-${hex.slice(20)}`;
}

function showActionResult(text, isError) {
  const line = document.getElementById("action-result");
  line.textContent = text;
  line.classList.toggle("error", Boolean(isError));
  line.hidden = false;
}

async function sendAction(action, params) {
  showActionResult(`${action}…`, false);
  try {
    const res = await fetch("/api/action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action_id: newActionId(), action, params }),
    });
    const data = await res.json().catch(() => null);
    if (data && data.status === "accepted") {
      showActionResult(
        `✓ ${data.message}${data.replayed ? " (replayed)" : ""}`, false);
    } else if (data && data.status === "rejected") {
      showActionResult(`✗ ${data.reason_code}: ${data.message}`, true);
    } else if (data && data.error) {
      showActionResult(`✗ ${data.error}`, true);
    } else {
      showActionResult(`✗ action failed (HTTP ${res.status})`, true);
    }
  } catch {
    showActionResult("✗ action request failed — server unreachable?", true);
  }
}

function actionButton(label, enabled, onClick) {
  const button = el("button", "action-button", label);
  if (!enabled) {
    button.disabled = true;
    button.title = DISABLED_TOOLTIP;
  } else {
    button.addEventListener("click", onClick);
  }
  return button;
}

function numberInput(placeholder) {
  const input = document.createElement("input");
  input.type = "number";
  input.min = "1";
  input.placeholder = placeholder;
  input.className = "action-input";
  return input;
}

function textInput(placeholder) {
  const input = document.createElement("input");
  input.type = "text";
  input.placeholder = placeholder;
  input.className = "action-input";
  return input;
}

function renderActionPanel(me, views) {
  if (!me || !me.signed_in) return; // panel lives inside the my-miner view
  const panel = document.getElementById("action-panel");
  const note = document.getElementById("action-note");
  const buttons = document.getElementById("action-buttons");
  panel.hidden = false;
  buttons.replaceChildren();
  const enabled = me.writes_configured === true;
  note.textContent = enabled
    ? "Actions run against the TEST economy only — never live guilds."
    : DISABLED_TOOLTIP;
  note.hidden = false;

  const simple = el("div", "action-row");
  for (const action of ["mine", "descend", "ascend"]) {
    simple.appendChild(
      actionButton(action, enabled, () => sendAction(action, {})));
  }
  buttons.appendChild(simple);

  const sellRow = el("div", "action-row");
  const sellItem = textInput("item (e.g. stone)");
  const sellQty = numberInput("qty");
  sellRow.append(sellItem, sellQty, actionButton("sell", enabled, () => {
    const quantity = parseInt(sellQty.value, 10);
    if (!sellItem.value || !(quantity >= 1)) {
      showActionResult("✗ sell needs an item name and a quantity ≥ 1", true);
      return;
    }
    sendAction("sell", { item: sellItem.value, quantity });
  }));
  buttons.appendChild(sellRow);

  const vaultRow = el("div", "action-row");
  const vaultAmount = numberInput("coins");
  const vaultAction = (action) => () => {
    const amount = parseInt(vaultAmount.value, 10);
    if (!(amount >= 1)) {
      showActionResult("✗ vault moves need an amount ≥ 1", true);
      return;
    }
    sendAction(action, { amount });
  };
  vaultRow.append(
    vaultAmount,
    actionButton("vault deposit", enabled, vaultAction("vault_deposit")),
    actionButton("vault withdraw", enabled, vaultAction("vault_withdraw")));
  buttons.appendChild(vaultRow);

  const equipRow = el("div", "action-row");
  const equipItem = textInput("item (e.g. iron pickaxe)");
  const equipSlot = document.createElement("select");
  equipSlot.className = "action-input";
  // Slot list is schema-derived server-side (/api/views `slots`) — the
  // dropdown can never drift from the contract's closed enum.
  for (const slot of views?.slots || []) {
    const option = document.createElement("option");
    option.value = slot;
    option.textContent = slot;
    equipSlot.appendChild(option);
  }
  equipRow.append(equipItem, equipSlot, actionButton("equip", enabled, () => {
    if (!equipItem.value) {
      showActionResult("✗ equip needs an item name", true);
      return;
    }
    sendAction("equip", { item: equipItem.value, slot: equipSlot.value });
  }));
  buttons.appendChild(equipRow);
}

function renderTestEconomyBadge(me) {
  // Persistent badge whenever writes are enabled: this site is pointed at
  // the TEST economy, and it should never be mistakable for live data.
  const badge = document.getElementById("test-economy-badge");
  badge.hidden = !(me && me.writes_configured === true);
}

async function fetchMe() {
  try {
    const res = await fetch("/api/me");
    if (!res.ok) throw new Error(`API responded ${res.status}`);
    return await res.json();
  } catch {
    return null; // auth endpoint down ≠ snapshot down — stay public
  }
}

async function boot() {
  let views = null;
  try {
    const res = await fetch("/api/views");
    if (!res.ok) throw new Error(`API responded ${res.status}`);
    views = await res.json();
    render(views);
  } catch (err) {
    showBanner(`Snapshot unavailable — ${err.message}. Nothing to render.`, true);
  }
  const me = await fetchMe();
  renderAuthControls(me);
  renderMyMiner(me, views);
  renderTestEconomyBadge(me);
  renderActionPanel(me, views);
}

boot();
