/* Mineverse stage-1 frontend — fetches /api/snapshot and renders it.
 * Field names mirror superbot's mining_player_state (mining_inventory,
 * depth, position, equipment, gear_wear, vault, vault_level, energy,
 * coins, skills, structures) + game_xp_service (xp). */

"use strict";

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

function itemList(store) {
  const entries = Object.entries(store || {});
  if (!entries.length) return [el("p", "empty", "(empty)")];
  const ul = el("ul", "items");
  for (const [name, qty] of entries.sort((a, b) => b[1] - a[1])) {
    ul.appendChild(el("li", null, `${qty}× ${name}`));
  }
  return [ul];
}

function kvList(store, formatter) {
  const entries = Object.entries(store || {});
  if (!entries.length) return [el("p", "empty", "(none)")];
  const ul = el("ul", "items");
  for (const [key, value] of entries) {
    ul.appendChild(el("li", null, formatter(key, value)));
  }
  return [ul];
}

function section(card, title, nodes) {
  card.appendChild(el("h4", null, title));
  nodes.forEach((n) => card.appendChild(n));
}

function renderMinerCard(miner, maxDepth, biomes) {
  const card = el("article", "card");
  card.appendChild(el("h3", null, miner.display_name || `miner ${miner.suid}`));
  card.appendChild(
    el("p", "depth-line",
      `Depth ${miner.depth}/${maxDepth} — ${biomeLabel(miner.depth, biomes)}` +
      (miner.position ? ` · at (${miner.position.x}, ${miner.position.y})` : "")),
  );
  const xp = miner.xp || {};
  card.appendChild(
    el("p", "xp-line",
      `Level ${xp.level ?? "?"} · ${xp.game_total ?? 0} mining XP · ` +
      `${miner.coins ?? 0} 🪙 · energy ${miner.energy ? miner.energy.current : "?"}`),
  );
  section(card, "Gear", kvList(miner.equipment, (slot, item) => {
    const wear = miner.gear_wear && miner.gear_wear[item];
    return `${slot}: ${item}${wear !== undefined ? ` (durability ${wear})` : ""}`;
  }));
  section(card, "Pack", itemList(miner.mining_inventory));
  section(card, `Vault (level ${miner.vault_level ?? 0})`, itemList(miner.vault));
  return card;
}

function renderDepthRace(miners, maxDepth, biomes) {
  const race = document.getElementById("depth-race");
  race.replaceChildren();
  for (const miner of [...miners].sort((a, b) => b.depth - a.depth)) {
    const row = el("div", "race-row");
    row.appendChild(el("span", "race-name", miner.display_name || miner.suid));
    const track = el("div", "race-track");
    const bar = el("div", "race-bar");
    bar.style.width = `${maxDepth ? (miner.depth / maxDepth) * 100 : 0}%`;
    track.appendChild(bar);
    row.appendChild(track);
    row.appendChild(el("span", "race-depth", biomeLabel(miner.depth, biomes)));
    race.appendChild(row);
  }
}

function renderLeaderboard(miners) {
  const tbody = document.querySelector("#leaderboard tbody");
  tbody.replaceChildren();
  const ranked = [...miners].sort(
    (a, b) => b.depth - a.depth || (b.xp?.game_total ?? 0) - (a.xp?.game_total ?? 0),
  );
  ranked.forEach((miner, i) => {
    const tr = el("tr");
    [i + 1, miner.display_name || miner.suid, miner.depth,
     miner.xp?.game_total ?? 0, miner.xp?.level ?? "?", miner.coins ?? 0]
      .forEach((cell) => tr.appendChild(el("td", null, String(cell))));
    tbody.appendChild(tr);
  });
}

function render(snapshot) {
  // READ contract v1 envelope (docs/mining-data-contract.md):
  // schema_version, generated_at, guild_id, miners[] (+ optional
  // max_depth/biomes world-shape hints, fallbacks below).
  const meta = document.getElementById("snapshot-meta");
  meta.textContent =
    `snapshot v${snapshot.schema_version ?? "?"} · ` +
    `generated ${snapshot.generated_at || "unknown"}`;

  const miners = snapshot.miners || [];
  if (!miners.length) {
    showBanner("Snapshot loaded, but it contains no miners.", false);
    return;
  }
  const maxDepth = snapshot.max_depth ?? FALLBACK_BIOMES.length - 1;

  renderDepthRace(miners, maxDepth, snapshot.biomes);
  renderLeaderboard(miners);
  const cards = document.getElementById("miner-cards");
  cards.replaceChildren();
  miners.forEach((m) => cards.appendChild(renderMinerCard(m, maxDepth, snapshot.biomes)));

  for (const id of ["depth-race-section", "leaderboard-section", "miners-section"]) {
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

function renderMyMiner(me, snapshot) {
  if (!me || !me.signed_in) return;
  const section = document.getElementById("my-miner-section");
  const note = document.getElementById("my-miner-note");
  const holder = document.getElementById("my-miner-card");
  section.hidden = false;
  if (me.miner) {
    const maxDepth = snapshot?.max_depth ?? FALLBACK_BIOMES.length - 1;
    holder.replaceChildren(renderMinerCard(me.miner, maxDepth, snapshot?.biomes));
  } else {
    note.textContent =
      `Signed in as ${me.user_id} — no miner found in this snapshot.`;
    note.hidden = false;
  }
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
  let snapshot = null;
  try {
    const res = await fetch("/api/snapshot");
    if (!res.ok) throw new Error(`API responded ${res.status}`);
    snapshot = await res.json();
    render(snapshot);
  } catch (err) {
    showBanner(`Snapshot unavailable — ${err.message}. Nothing to render.`, true);
  }
  const me = await fetchMe();
  renderAuthControls(me);
  renderMyMiner(me, snapshot);
}

boot();
