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

function hideBanner() {
  const banner = document.getElementById("status-banner");
  banner.textContent = "";
  banner.classList.remove("error");
  banner.hidden = true;
}

function biomeName(depth, biomes) {
  // Plain biome name, no emoji — for surfaces that want text only
  // (e.g. the canvas share card, where emoji glyphs are unreliable).
  const names = Array.isArray(biomes) && biomes.length ? biomes : FALLBACK_BIOMES;
  return names[Math.max(0, Math.min(depth, names.length - 1))];
}

function biomeLabel(depth, biomes) {
  const names = Array.isArray(biomes) && biomes.length ? biomes : FALLBACK_BIOMES;
  const idx = Math.max(0, Math.min(depth, names.length - 1));
  return `${BIOME_ICONS[idx] || ""} ${names[idx]}`.trim();
}

function visuallyHidden(tag, text) {
  // Screen-reader-only text alternative (styled by .visually-hidden).
  return el(tag, "visually-hidden", text);
}

function decorative(node) {
  // Purely visual — hidden from assistive tech; a text alternative
  // conveying the same info must sit next to it.
  node.setAttribute("aria-hidden", "true");
  return node;
}

function prefersReducedMotion() {
  // Shared JS-side motion gate (the CSS-side twin is the global
  // prefers-reduced-motion block in style.css). Any script-driven
  // animation must check this and render its final state instantly.
  return typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/* --- fun layer: console greeting (plain string, printed once at boot) ---- */

const CONSOLE_GREETING = [
  "        _____________________",
  "       /  welcome to the     \\",
  "      |   M I N E V E R S E   |",
  "       \\_____________________/",
  "  ~~~~~~~~~|  |~~~~~~~~~~~~~~~~~~~~",
  "   surface |  |  <- you are here",
  "  ---------|  |--------------------",
  "   cavern  |  |      o   o",
  "  ---------|  |--------------------",
  "   the deep|  |          *  .  *",
  "  ---------|  |--------------------",
  "   magma   |__|  dig safely, miner",
  "  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~",
].join("\n");

/* --- fun layer: Konami code → diamond rain -------------------------------
 * ↑↑↓↓←→←→BA anywhere on the page starts a brief aria-hidden shower of
 * the diamond ore SVG. Fixed-position + pointer-events:none, so no
 * layout shift and nothing becomes unclickable; Escape dismisses early;
 * it always cleans itself up. Under prefersReducedMotion() the shower
 * is an instant static flash (no falling animation) that clears fast. */

const KONAMI_SEQUENCE = [
  "ArrowUp", "ArrowUp", "ArrowDown", "ArrowDown",
  "ArrowLeft", "ArrowRight", "ArrowLeft", "ArrowRight",
  "b", "a",
];
const DIAMOND_RAIN_DROPS = 24;
const DIAMOND_RAIN_MS = 4000;
const DIAMOND_FLASH_MS = 1200; // reduced-motion static flash duration
let konamiProgress = 0;
let diamondRainTimer = null;

function dismissDiamondRain() {
  const overlay = document.getElementById("diamond-rain");
  if (overlay) overlay.remove();
  if (diamondRainTimer !== null) {
    clearTimeout(diamondRainTimer);
    diamondRainTimer = null;
  }
}

function startDiamondRain() {
  dismissDiamondRain(); // never stack two showers
  const reduced = prefersReducedMotion();
  const overlay = decorative(el("div", "diamond-rain"));
  overlay.id = "diamond-rain";
  for (let i = 0; i < DIAMOND_RAIN_DROPS; i++) {
    const drop = svgSpan("diamond-drop", oreIconSVG("diamond"));
    // Deterministic scatter — no randomness, the same shower every time.
    drop.style.left = `${(i * 37) % 100}%`;
    if (reduced) {
      // Static flash: diamonds appear in place, no motion at all.
      drop.style.top = `${(i * 53) % 90}%`;
    } else {
      drop.style.animationDelay = `${(i % 8) * 0.15}s`;
      drop.classList.add("falling");
    }
    overlay.appendChild(drop);
  }
  document.body.appendChild(overlay);
  diamondRainTimer = setTimeout(
    dismissDiamondRain, reduced ? DIAMOND_FLASH_MS : DIAMOND_RAIN_MS);
}

function konamiNextProgress(progress, key, sequence) {
  // Pure KMP-style step. The keys seen so far are sequence[0..progress-1]
  // followed by `key`; the next progress is the LONGEST prefix of the
  // sequence that is a suffix of that input. A plain reset-to-0-or-1 on
  // mismatch loses real progress — e.g. a third ArrowUp after ↑↑ must
  // keep progress 2, not fall back to 1. Ten keys, so the scan is free.
  for (let len = Math.min(progress + 1, sequence.length); len > 0; len--) {
    if (sequence[len - 1] !== key) continue;
    let matches = true;
    for (let i = 0; i < len - 1; i++) {
      if (sequence[i] !== sequence[progress - len + 1 + i]) {
        matches = false;
        break;
      }
    }
    if (matches) return len;
  }
  return 0;
}

function onKonamiKeydown(event) {
  if (event.key === "Escape") {
    dismissDiamondRain();
    return;
  }
  const key = event.key.length === 1 ? event.key.toLowerCase() : event.key;
  konamiProgress = konamiNextProgress(konamiProgress, key, KONAMI_SEQUENCE);
  if (konamiProgress === KONAMI_SEQUENCE.length) {
    konamiProgress = 0;
    startDiamondRain();
  }
}

document.addEventListener("keydown", onKonamiKeydown);

/* --- fun layer: polite toast (role=status live region in index.html) ----- */

let toastTimer = null;

function showToast(text) {
  const toast = document.getElementById("toast");
  toast.textContent = text;
  toast.hidden = false;
  if (toastTimer !== null) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toast.hidden = true; }, 5000);
}

/* --- fun layer: Tool Fondler (activate a miner's tool row 10×) -----------
 * The tool row is a REAL button (keyboard-activatable for free); the
 * counter is per miner and the achievement fires once per page load —
 * no persistence, it's a toy. The sparkle animates only when motion is
 * allowed; the toast is the accessible announcement either way. */

const TOOL_FONDLER_CLICKS = 10;
const toolClicks = new Map(); // suid -> activations this page load
const toolFondlerDone = new Set();

function onToolRowActivated(suid, row) {
  if (toolFondlerDone.has(suid)) return;
  const clicks = (toolClicks.get(suid) || 0) + 1;
  toolClicks.set(suid, clicks);
  if (clicks < TOOL_FONDLER_CLICKS) return;
  toolFondlerDone.add(suid);
  const sparkle = decorative(el("span", "sparkle", " ✨"));
  if (!prefersReducedMotion()) sparkle.classList.add("sparkle-pop");
  row.appendChild(sparkle);
  showToast(
    "Hidden achievement: Tool Fondler — that pickaxe is now extremely polished.");
}

function toolRowButton(suid) {
  const button = el("button", "tool-row");
  button.type = "button";
  button.addEventListener("click", () => onToolRowActivated(suid, button));
  return button;
}

/* --- ambient cave audio (WebAudio, synthesized, muted by default) --------
 * No audio asset files: the ambience is SYNTHESIZED — a looped low-pass-
 * filtered noise buffer for cave wind plus occasional soft sine "drips"
 * on a decay envelope, all whisper-quiet. MUTED BY DEFAULT, always: the
 * AudioContext is created only inside the toggle's click handler, so no
 * sound can exist before an explicit opt-in (no-autoplay discipline; the
 * browser gesture requirement agrees). The toggle is a real button whose
 * aria-pressed + visible label mirror the TRUE audio state; the choice
 * does not persist across reloads (nothing in web/ persists UI state).
 * Nothing on the page pulses or animates with the audio, so there is
 * nothing extra to gate under prefers-reduced-motion — the toggle stays
 * available and the single motion gate stays single. */

const CAVE_AUDIO = {
  masterGain: 0.04, // whisper-quiet — ambience, never music
  wind: {
    noiseSeconds: 2, // looped noise buffer length
    filterType: "lowpass",
    frequencyHz: 240, // deep rumble, no hiss
    q: 0.8,
  },
  drip: {
    oscillatorType: "sine",
    startHz: 1100, // droplet "plink": a falling pitch...
    endHz: 380,
    decaySeconds: 0.5, // ...that dies away fast
    peakGain: 0.35, // relative to the master gain
    minGapSeconds: 4,
    maxGapSeconds: 9,
  },
};

function caveSoundsButtonState(on) {
  // PURE (JSON in, JSON out — pinned by tests/test_js_logic.py): audio
  // state → the honest button face. aria-pressed mirrors the REAL state
  // and the visible label says the same thing in words.
  return on
    ? { pressed: "true", label: "🔊 Cave sounds on" }
    : { pressed: "false", label: "🔇 Cave sounds off" };
}

function caveAmbienceGraphSpec(config) {
  // PURE (config in, JSON out — pinned by tests/test_js_logic.py): the
  // audio-graph SPEC for the wind bed — node descriptions plus the
  // connection chain — kept separate from the WebAudio wiring so the
  // graph shape is testable without an AudioContext.
  // startCaveAmbience is a thin interpreter of this spec. Called with
  // no argument it describes the SHIPPED ambience (CAVE_AUDIO).
  const c = config || CAVE_AUDIO;
  return {
    nodes: [
      { id: "master", type: "gain", gain: c.masterGain },
      { id: "wind-filter", type: "biquad", filterType: c.wind.filterType,
        frequencyHz: c.wind.frequencyHz, q: c.wind.q },
      { id: "wind-noise", type: "noise", seconds: c.wind.noiseSeconds,
        loop: true },
    ],
    connections: [
      ["wind-noise", "wind-filter"],
      ["wind-filter", "master"],
      ["master", "destination"],
    ],
  };
}

function caveDripDelaySeconds(index, config) {
  // PURE: drip counter → seconds until the next drip. Deterministic
  // scatter (same trick as the diamond rain — no randomness), cycling
  // through every gap in [minGapSeconds, maxGapSeconds]: the cave drips
  // the same rhythm for everyone, every visit.
  const drip = (config || CAVE_AUDIO).drip;
  const span = drip.maxGapSeconds - drip.minGapSeconds + 1;
  return drip.minGapSeconds + ((index * 5) % span);
}

let caveAudioCtx = null; // created ONLY inside the toggle click handler
let caveAudioNodes = null;
let caveDripTimer = null;
let caveDripIndex = 0;

function buildCaveAudioNode(ctx, spec) {
  // Thin interpreter, one spec node → one WebAudio node.
  if (spec.type === "gain") {
    const node = ctx.createGain();
    node.gain.value = spec.gain;
    return node;
  }
  if (spec.type === "biquad") {
    const node = ctx.createBiquadFilter();
    node.type = spec.filterType;
    node.frequency.value = spec.frequencyHz;
    node.Q.value = spec.q;
    return node;
  }
  if (spec.type === "noise") {
    // Deterministic noise (a fixed-seed LCG — no randomness anywhere,
    // the diamond-rain house rule): the same wind every visit.
    const frames = Math.max(1, Math.round(spec.seconds * ctx.sampleRate));
    const buffer = ctx.createBuffer(1, frames, ctx.sampleRate);
    const data = buffer.getChannelData(0);
    let seed = 0x2f6e2b1;
    for (let i = 0; i < frames; i++) {
      seed = (seed * 1664525 + 1013904223) >>> 0;
      data[i] = (seed / 0xffffffff) * 2 - 1;
    }
    const node = ctx.createBufferSource();
    node.buffer = buffer;
    node.loop = Boolean(spec.loop);
    return node;
  }
  return null;
}

function playCaveDrip(ctx, destination) {
  const drip = CAVE_AUDIO.drip;
  const now = ctx.currentTime;
  const osc = ctx.createOscillator();
  osc.type = drip.oscillatorType;
  osc.frequency.setValueAtTime(drip.startHz, now);
  osc.frequency.exponentialRampToValueAtTime(
    drip.endHz, now + drip.decaySeconds);
  const envelope = ctx.createGain();
  envelope.gain.setValueAtTime(drip.peakGain, now);
  envelope.gain.exponentialRampToValueAtTime(
    0.001, now + drip.decaySeconds);
  osc.connect(envelope);
  envelope.connect(destination);
  osc.start(now);
  osc.stop(now + drip.decaySeconds); // one-shot: stops and frees itself
}

function scheduleNextCaveDrip() {
  caveDripTimer = setTimeout(() => {
    if (!caveAudioCtx) return; // toggled off while waiting
    playCaveDrip(caveAudioCtx, caveAudioNodes.master);
    caveDripIndex += 1;
    scheduleNextCaveDrip();
  }, caveDripDelaySeconds(caveDripIndex) * 1000);
}

function startCaveAmbience() {
  // Called ONLY from the toggle's click handler — the AudioContext is
  // born inside the user's gesture, never at load. Returns whether audio
  // actually started, so the button face can stay honest when the
  // browser has no WebAudio at all.
  const Ctor = window.AudioContext || window.webkitAudioContext;
  if (typeof Ctor !== "function") return false;
  const ctx = new Ctor();
  if (typeof ctx.resume === "function") ctx.resume();
  const spec = caveAmbienceGraphSpec();
  const nodes = Object.create(null);
  for (const nodeSpec of spec.nodes) {
    nodes[nodeSpec.id] = buildCaveAudioNode(ctx, nodeSpec);
  }
  for (const [from, to] of spec.connections) {
    const source = nodes[from];
    const target = to === "destination" ? ctx.destination : nodes[to];
    if (source && target) source.connect(target);
  }
  nodes["wind-noise"].start();
  caveAudioCtx = ctx;
  caveAudioNodes = nodes;
  caveDripIndex = 0;
  scheduleNextCaveDrip();
  return true;
}

function stopCaveAmbience() {
  if (caveDripTimer !== null) {
    clearTimeout(caveDripTimer);
    caveDripTimer = null;
  }
  if (caveAudioCtx && typeof caveAudioCtx.close === "function") {
    caveAudioCtx.close(); // silences the wind and frees the device
  }
  caveAudioCtx = null;
  caveAudioNodes = null;
}

function paintCaveSoundsToggle(button, on) {
  const state = caveSoundsButtonState(on);
  button.setAttribute("aria-pressed", state.pressed);
  button.textContent = state.label;
}

function onCaveSoundsToggle(event) {
  const button = event.currentTarget;
  if (caveAudioCtx) {
    stopCaveAmbience();
    paintCaveSoundsToggle(button, false);
  } else {
    // startCaveAmbience reports honestly — no WebAudio, no "on" label.
    paintCaveSoundsToggle(button, startCaveAmbience());
  }
}

const caveSoundsButton = document.getElementById("cave-audio-toggle");
if (caveSoundsButton) {
  caveSoundsButton.addEventListener("click", onCaveSoundsToggle);
  paintCaveSoundsToggle(caveSoundsButton, false); // muted by default, always
}

/* --- inline-SVG decoration (cave theme) ----------------------------------
 * Every icon here is a graphical repeat of text that sits next to it, so
 * each one routes through decorative() — never a replacement for text. */

function svgSpan(className, markup) {
  const span = el("span", className);
  span.innerHTML = markup;
  return decorative(span);
}

// Ore rarity identity: one distinct color per contract ore tier
// (display-order stone → diamond mirrors server/views.py ORE_TIER_ORDER).
const ORE_TIER_COLORS = {
  stone: "#9aa0a6",
  bronze: "#c07f45",
  iron: "#aeb6c2",
  silver: "#eceff4",
  gold: "#f5c842",
  diamond: "#7de8e0",
};

function oreIconSVG(name) {
  // Aria-hidden gem icon for the six ore tiers; unknown item names are
  // contractually open, so they simply get no icon (null).
  const color = ORE_TIER_COLORS[name];
  if (!color) return null;
  return `<svg viewBox="0 0 10 10" width="11" height="11" focusable="false">` +
    `<polygon points="5,0.5 9.5,4 5,9.5 0.5,4" fill="${color}"/>` +
    `<polygon points="5,0.5 9.5,4 5,4" fill="#ffffff" opacity="0.25"/>` +
    `</svg>`;
}

function hatSVGRects(pixels) {
  // PURE (JSON in, string out — pinned per-CI-run by
  // tests/test_js_logic.py): a server-derived hat pixel spec
  // (server/views.py HAT_CATALOG `pixels`) → SVG <rect> markup drawn
  // OVER the avatar base. Tolerant of junk: a non-array spec renders
  // as "" (no hat), and every entry must be [x, y, w, h, "#hex"] with
  // finite numbers and a safe hex color — anything else is skipped, so
  // no unvetted string ever lands in markup.
  if (!Array.isArray(pixels)) return "";
  return pixels
    .filter((p) => Array.isArray(p) && p.length === 5 &&
      p.slice(0, 4).every(Number.isFinite) &&
      typeof p[4] === "string" && /^#[0-9a-fA-F]{3,8}$/.test(p[4]))
    .map(([x, y, w, h, color]) =>
      `<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${color}"/>`)
    .join("");
}

function hatsByName(hats) {
  // PURE (JSON in, JSON out — pinned by tests/test_js_logic.py):
  // /api/views `hats` → { display_name: catalog entry }. Joins the
  // per-miner rows to the catalog by hat id; rows with an unknown hat
  // id or no name drop out honestly (a nameless hat can't reach a
  // chip). display_name matches build_ladder's fallback server-side,
  // so the join onto ladder chips is exact.
  const catalog = Object.create(null);
  for (const entry of (hats && Array.isArray(hats.catalog)) ? hats.catalog : []) {
    if (entry && typeof entry.id === "string") catalog[entry.id] = entry;
  }
  const byName = Object.create(null);
  for (const row of (hats && Array.isArray(hats.miners)) ? hats.miners : []) {
    if (!row || typeof row.display_name !== "string") continue;
    const entry = catalog[row.hat];
    if (entry) byName[row.display_name] = entry;
  }
  return byName;
}

function pixelSVGShell(viewBox, width, height, inner, crisp = true) {
  // THE shared shell for the hand-rolled pixel-art icons — one place
  // owns `focusable="false"` (a fifth icon can never forget it) and the
  // default crispEdges pixel look. `crisp = false` is for the one
  // smooth-stroke mark (crackedIconSVG) that never shipped crispEdges;
  // byte-for-byte equivalent to the four literals it replaced.
  return `<svg viewBox="${viewBox}" width="${width}" height="${height}" ` +
    (crisp ? `shape-rendering="crispEdges" ` : ``) +
    `focusable="false">` + inner + `</svg>`;
}

function minerAvatarSVG(hat) {
  // Pixel-style miner (helmet, face, overalls) for the depth shaft.
  // Grid is 8×10: rows 0–1 are hat headroom, row 2 the base helmet row
  // (server/views.py HAT_GRID_WIDTH/HEIGHT pin the same numbers). The
  // optional server-derived cosmetic hat draws AFTER the base so its
  // pixels layer on top.
  return pixelSVGShell("0 0 8 10", 12, 15,
    `<rect x="2" y="2" width="4" height="1" fill="#f5a83c"/>` +
    `<rect x="2" y="3" width="4" height="2" fill="#e8c9a0"/>` +
    `<rect x="1" y="5" width="6" height="3" fill="#4a6fa5"/>` +
    `<rect x="2" y="8" width="1" height="2" fill="#3a3350"/>` +
    `<rect x="5" y="8" width="1" height="2" fill="#3a3350"/>` +
    hatSVGRects(hat ? hat.pixels : null));
}

function recordFlagSVG() {
  // Marker flag planted at a record-depth band.
  return pixelSVGShell("0 0 8 10", 10, 12,
    `<rect x="1" y="0" width="1" height="10" fill="#a79fc0"/>` +
    `<polygon points="2,0 8,2 2,4" fill="#e2543e"/>`);
}

function vaultChestSVG(level, levelMax) {
  // Chest that fills stepwise by vault level; the fill height is the
  // level fraction of the chest body (empty at 0, brim-full at max).
  const bounded = Math.max(0, Math.min(level, levelMax));
  const fraction = levelMax > 0 ? bounded / levelMax : 0;
  const bodyTop = 4;
  const bodyHeight = 6;
  const fillH = Math.round(bodyHeight * fraction);
  return `<svg viewBox="0 0 12 11" width="14" height="13" focusable="false">` +
    `<rect x="1" y="1" width="10" height="3" rx="1" fill="#c07f45"/>` +
    `<rect x="1" y="${bodyTop}" width="10" height="${bodyHeight}" ` +
    `fill="#221d2e" stroke="#c07f45" stroke-width="1"/>` +
    (fillH > 0
      ? `<rect x="2" y="${bodyTop + bodyHeight - fillH - 0.5}" width="8" ` +
        `height="${fillH}" fill="#f5c842"/>`
      : "") +
    `<rect x="5" y="3" width="2" height="2" fill="#f5a83c"/>` +
    `</svg>`;
}

function lanternSVG(fraction) {
  // Lantern whose glow dims stepwise toward 0 with the energy fraction
  // (5 steps) — an as-of-snapshot picture, never ticked forward.
  const step = Math.max(0, Math.min(4, Math.round(fraction * 4)));
  const glowRadius = [0.6, 1.6, 2.6, 3.6, 4.6][step];
  const glowOpacity = [0.06, 0.16, 0.28, 0.4, 0.5][step];
  const flameOpacity = 0.25 + 0.75 * (step / 4);
  return `<svg viewBox="0 0 12 14" width="13" height="15" focusable="false">` +
    `<circle cx="6" cy="8" r="${glowRadius}" fill="#f5c842" ` +
    `opacity="${glowOpacity}"/>` +
    `<rect x="4.5" y="1" width="3" height="1.5" fill="#8a8296"/>` +
    `<rect x="3.5" y="2.5" width="5" height="8.5" rx="1.2" fill="none" ` +
    `stroke="#8a8296" stroke-width="1"/>` +
    `<circle cx="6" cy="8" r="1.5" fill="#f5c842" opacity="${flameOpacity}"/>` +
    `</svg>`;
}

function crackedIconSVG() {
  // Broken-gear crack mark (shown only at/over the wear display cap).
  // crisp=false: the crack is a smooth diagonal stroke and has never
  // shipped crispEdges — keeping the bytes identical is the point.
  return pixelSVGShell("0 0 8 10", 9, 11,
    `<polyline points="4,0 2.5,4 5.5,5.5 3,10" fill="none" ` +
    `stroke="#e2543e" stroke-width="1.4"/>`,
    false);
}

/* --- seasonal decorations (date-keyed cosmetic layer, backlog item 6) ----
 * A small cosmetic layer over the cave theme keyed to the calendar DATE:
 * one pixel-art ornament in the header slot (aria-hidden — pure flavor,
 * like the diamond rain, it carries no information) plus a body class
 * that retints the EXISTING lantern glow (--glow). The date is INJECTED:
 * seasonForDate / seasonalDecorSpec / seasonalDecorSVG are pure functions
 * (pinned per-CI-run by tests/test_js_logic.py); only applySeasonalDecor
 * touches the DOM, and only boot() reads the real clock, once. Purely
 * cosmetic — no gameplay meaning, NO new animation (the lantern-flicker
 * keyframes + global reduced-motion guard predate this layer), nothing
 * persists. */

const SEASONAL_EVENTS = [
  // Fixed fun dates — checked before the season windows, so they win.
  { id: "founding-day", dates: ["07-11"] }, // this repo's founding day
  { id: "new-year", dates: ["12-31", "01-01"] },
];

const SEASON_WINDOWS = [
  // Inclusive "MM-DD" windows; winter wraps the year end (from > to).
  { id: "winter", from: "12-01", to: "02-29" },
  { id: "spring", from: "03-01", to: "05-31" },
  { id: "summer", from: "06-01", to: "08-31" },
  { id: "autumn", from: "09-01", to: "11-30" },
];

function seasonForDate(isoDate) {
  // PURE (string in, id/null out — pinned by tests/test_js_logic.py):
  // "YYYY-MM-DD..." → season/event id. Comparisons run on the "MM-DD"
  // slice (lexicographic == chronological for zero-padded fields), so
  // the mapping repeats identically every year; a malformed or
  // impossible month/day returns null and the page simply stays
  // undecorated — never a throw at boot.
  const match = typeof isoDate === "string"
    ? /^\d{4}-((?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01]))(?:$|[T\s])/.exec(isoDate)
    : null;
  if (!match) return null;
  const mmdd = match[1];
  for (const event of SEASONAL_EVENTS) {
    if (event.dates.includes(mmdd)) return event.id;
  }
  for (const range of SEASON_WINDOWS) {
    const inside = range.from <= range.to
      ? mmdd >= range.from && mmdd <= range.to
      : mmdd >= range.from || mmdd <= range.to; // wraps the year end
    if (inside) return range.id;
  }
  return null; // unreachable with the windows above — honest anyway
}

// Pixel art per season/event on the miner-avatar 10×10 grid, in the hat
// [x, y, w, h, "#hex"] grammar — hatSVGRects supplies the rect markup and
// its junk filter, and every color is an existing palette hex (ore tiers,
// biome tints, cave edge/accent). Small on purpose: one ~15px ornament.
const SEASONAL_DECOR = {
  winter: {
    label: "cave icicles",
    pixels: [
      [0, 0, 10, 1, "#3a3350"], // cave ceiling lip
      [1, 1, 2, 4, "#7de8e0"], [1, 5, 1, 2, "#7de8e0"], // long icicle
      [4, 1, 2, 3, "#7de8e0"], [4, 4, 1, 1, "#7de8e0"], // mid icicle
      [7, 1, 2, 2, "#7de8e0"], [7, 3, 1, 1, "#7de8e0"], // short icicle
      [1, 1, 1, 2, "#eceff4"], // glint
    ],
  },
  spring: {
    label: "cave moss sprout",
    pixels: [
      [0, 9, 10, 1, "#3a3350"], // cave floor
      [4, 4, 2, 5, "#6cc46c"], // stem
      [2, 3, 2, 2, "#7dc46c"], [6, 3, 2, 2, "#7dc46c"], // side leaves
      [4, 1, 2, 2, "#7dc46c"], // crown leaf
    ],
  },
  summer: {
    label: "sun crystal",
    pixels: [
      [4, 1, 2, 1, "#f5c842"],
      [3, 2, 4, 1, "#f5c842"],
      [2, 3, 6, 2, "#f5c842"],
      [3, 5, 4, 1, "#f5c842"],
      [4, 6, 2, 1, "#f5c842"],
      [4, 2, 1, 1, "#eceff4"], // glint
    ],
  },
  autumn: {
    label: "amber leaf",
    pixels: [
      [4, 1, 2, 1, "#e2543e"],
      [3, 2, 4, 2, "#e2543e"],
      [2, 4, 6, 2, "#c07f45"],
      [3, 6, 4, 1, "#c07f45"],
      [4, 7, 1, 2, "#c07f45"], // stem
    ],
  },
  "founding-day": {
    label: "founding-day pennant",
    pixels: [
      [1, 0, 1, 10, "#a79fc0"], // pole (record-flag grey)
      [2, 0, 6, 2, "#f5a83c"], // pennant, accent gold
      [2, 2, 4, 2, "#f5a83c"],
      [2, 4, 2, 1, "#f5a83c"], // taper
    ],
  },
  "new-year": {
    label: "new-year star",
    pixels: [
      [4, 1, 2, 2, "#eceff4"], [4, 7, 2, 2, "#eceff4"], // vertical arms
      [1, 4, 2, 2, "#eceff4"], [7, 4, 2, 2, "#eceff4"], // horizontal arms
      [3, 3, 4, 4, "#eceff4"], // body
      [4, 4, 2, 2, "#f5c842"], // gold core (drawn over the body)
    ],
  },
};

function seasonalDecorSpec(seasonId) {
  // PURE (id in, JSON out — pinned by tests/test_js_logic.py): season or
  // event id → renderable spec { id, label, cssClass, pixels }. Unknown
  // or null id → null: "no decoration" is always a valid outcome.
  const art = SEASONAL_DECOR[seasonId];
  if (!art) return null;
  return {
    id: seasonId,
    label: art.label,
    cssClass: `season-${seasonId}`,
    pixels: art.pixels,
  };
}

function seasonalDecorSVG(spec) {
  // PURE: spec → inline pixel-SVG markup on the miner-avatar aesthetic
  // (10×10 grid, crispEdges). hatSVGRects is the single rect grammar +
  // junk filter, so nothing unvetted ever lands in markup here either.
  if (!spec || !Array.isArray(spec.pixels)) return "";
  const rects = hatSVGRects(spec.pixels);
  if (!rects) return "";
  return pixelSVGShell("0 0 10 10", 15, 15, rects);
}

function applySeasonalDecor(isoDate) {
  // Impure caller — the ONLY place the (injected) date meets the DOM.
  // Adds the body tint class + fills the static aria-hidden header slot;
  // no season (null) leaves the page byte-for-byte as it always was.
  const spec = seasonalDecorSpec(seasonForDate(isoDate));
  if (!spec) return;
  document.body.classList.add(spec.cssClass);
  const slot = document.getElementById("seasonal-decor-slot");
  if (slot) slot.innerHTML = seasonalDecorSVG(spec);
}

function bandLabel(depth, biome) {
  // Shared ladder/mini-map band label: the biome emoji is decorative
  // (the biome NAME carries the meaning), so it is aria-hidden.
  const label = el("div", "ladder-label");
  const biomeSpan = el("span", "ladder-biome");
  const icon = BIOME_ICONS[depth];
  if (icon) biomeSpan.appendChild(decorative(el("span", null, `${icon} `)));
  biomeSpan.appendChild(document.createTextNode(biome));
  label.appendChild(biomeSpan);
  label.appendChild(el("span", "ladder-depth", `depth ${depth}`));
  return label;
}

/* --- snapshot staleness (header) ----------------------------------------- */

function formatAge(seconds) {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`;
  return `${Math.floor(seconds / 86400)}d`;
}

function groupDigits(n) {
  // Group a numeric stat's digits for display (18450 -> "18,450"). Locale is
  // PINNED to en-US so served bytes stay deterministic; anything that isn't a
  // finite number passes through String() unchanged (so undefined/null-derived
  // values render exactly as they did before). Display-only.
  return (typeof n === "number" && Number.isFinite(n))
    ? n.toLocaleString("en-US")
    : String(n);
}

function renderStaleness(staleness) {
  // Age is computed HERE, against the browser clock, once per page load —
  // no live ticking. The server only ships generated_at (+ its epoch) and
  // the contract-prose thresholds (60 s cadence, stale beyond ~180 s —
  // docs/mining-data-contract.md § Delivery expectations).
  const line = document.getElementById("snapshot-staleness");
  line.hidden = false;
  line.classList.remove("fresh", "warn", "stale", "sample");
  if (staleness?.source === "sample") {
    // The committed demo file is old BY DESIGN — the STALE alarm would
    // be a permanent false positive. Name the situation, and surface the
    // sample's vintage (sample_generated_at, date-only) so HOW OLD the
    // demo data is stays transparent instead of hidden.
    line.classList.add("sample");
    let text = "committed sample data — live relay not connected";
    const vintage = staleness?.sample_generated_at;
    if (typeof vintage === "string" && vintage) {
      text += ` · generated ${vintage.slice(0, 10)}`;
    }
    line.textContent = text;
    return;
  }
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
    const li = el("li", i < oreCount ? `ore tier-${name}` : null);
    const icon = i < oreCount ? oreIconSVG(name) : null;
    if (icon) li.appendChild(svgSpan("ore-icon", icon));
    li.appendChild(document.createTextNode(`${qty}× ${name}`));
    ul.appendChild(li);
  });
  return [ul];
}

// Display cap for the gear-wear bar ONLY. The contract says gear_wear is
// ACCUMULATED wear (0 = pristine, integer ≥ 0, no schema maximum), so the
// bar fills toward broken and clamps at this cap; the exact wear number
// stays visible as text either way.
const WEAR_DISPLAY_MAX = 100;

function wearBar(wear) {
  // Green → amber → red durability bar; cracked/broken state at the cap.
  // Decorative: the "· wear N" text next to it carries the real value.
  const track = decorative(el("span", "wear-track"));
  const bar = el("span", "wear-bar");
  const clamped = Math.max(0, Math.min(wear, WEAR_DISPLAY_MAX));
  bar.style.width = `${(clamped / WEAR_DISPLAY_MAX) * 100}%`;
  bar.classList.add(
    wear >= 80 ? "wear-critical" : wear >= 50 ? "wear-worn" : "wear-ok");
  track.appendChild(bar);
  return track;
}

function gearList(gear, suid) {
  // gear = [{slot, item|null, wear|null}] — every schema slot, always.
  if (!Array.isArray(gear) || !gear.length) {
    return [el("p", "empty", "(no gear data)")];
  }
  const ul = el("ul", "items gear-list");
  for (const { slot, item, wear } of gear) {
    const li = el("li", item ? null : "slot-empty");
    // The equipped tool row is a real button (styled as plain text) so
    // the hidden Tool Fondler achievement is keyboard-activatable; the
    // row's content and semantics are otherwise identical.
    const row = slot === "tool" && item && suid != null
      ? toolRowButton(suid)
      : li;
    row.appendChild(el("span", "slot-name", slot));
    const hasWear = wear !== null && wear !== undefined;
    row.appendChild(el("span", null, item
      ? ` ${item}${hasWear ? ` · wear ${wear}` : ""}`
      : " — empty"));
    if (item && hasWear && typeof wear === "number") {
      row.appendChild(wearBar(wear));
      if (wear >= WEAR_DISPLAY_MAX) {
        li.classList.add("gear-broken");
        row.appendChild(svgSpan("cracked-icon", crackedIconSVG()));
        row.appendChild(visuallyHidden("span", " (broken)"));
      }
    }
    if (row !== li) li.appendChild(row);
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
  const known = typeof current === "number" && typeof max === "number" && max > 0;
  // Lantern glow dims with the energy fraction — a graphical repeat of
  // the label numbers, so decorative; skipped when energy is unknown.
  if (known) {
    row.appendChild(svgSpan("energy-lantern",
      lanternSVG(Math.max(0, Math.min(current / max, 1)))));
  }
  row.appendChild(el("span", "energy-label", `⚡ ${current ?? "?"}/${max ?? "?"}`));
  // The bar repeats the current/max numbers graphically — decorative.
  const track = decorative(el("div", "energy-track"));
  const bar = el("div", "energy-bar");
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

function tableHeadRow(cells) {
  // Shared scoped column-header row for every hand-rolled table
  // (leaderboard, inventory matrix, VS view): text in, one <tr> of
  // scope=col <th>s out — the three builders can't drift apart on scope.
  const tr = el("tr");
  for (const cell of cells) {
    const th = el("th", null, cell);
    th.scope = "col";
    tr.appendChild(th);
  }
  return tr;
}

function section(card, title, nodes) {
  card.appendChild(el("h4", null, title));
  nodes.forEach((n) => card.appendChild(n));
}

function snapshotIsStale(staleness) {
  // The SAME age math renderStaleness paints in the header: age against
  // the browser clock once at render time, never ticked forward. An
  // unknown timestamp reads as NOT stale — the header already announces
  // "age unknown" honestly, so the cards don't pile on a guess.
  // Sample data is old by design (see renderStaleness) — the demo's
  // miners are not "idle", so the 💤 marks stay off entirely.
  if (staleness?.source === "sample") return false;
  const epoch = staleness?.generated_at_epoch;
  if (typeof epoch !== "number") return false;
  const age = Math.floor(Date.now() / 1000) - epoch;
  return age >= (staleness?.stale_after_seconds ?? 180);
}

/* --- share card (canvas → PNG download, fully client-side) ---------------
 * A real <button> on every miner card draws the miner's headline stats
 * onto an OFFSCREEN canvas (cave palette mirrored from style.css, gem
 * flourish reusing the oreIconSVG geometry + ORE_TIER_COLORS) and saves
 * it as a PNG via a temporary <a download>. No network, no dependency;
 * the drawing is a single static frame, so there is nothing to gate on
 * reduced motion — no animation is ever created. */

const SHARE_CARD_WIDTH = 640;
const SHARE_CARD_HEIGHT = 360;

// Canvas twin of the style.css cave palette (canvas can't read CSS vars
// from a stylesheet it isn't attached to, so the hexes are mirrored).
const SHARE_CARD_THEME = {
  bgTop: "#17141f", // --bg
  bgBottom: "#0e0c14", // --bg-deep
  panel: "#221d2e", // --panel
  edge: "#3a3350", // --edge
  text: "#e8e4f2", // --text
  muted: "#a79fc0", // --muted
  accent: "#f5a83c", // --accent
};

function shareCardGearLines(gear) {
  // Key gear = equipped slots only, capped so the card never overflows.
  return (Array.isArray(gear) ? gear : [])
    .filter((entry) => entry && entry.item)
    .slice(0, 4)
    .map(({ slot, item, wear }) =>
      `${slot}: ${item}${typeof wear === "number" ? ` · wear ${wear}` : ""}`);
}

function shareCardLines(miner, world) {
  // Pure text-shaping seam: everything the canvas paints, as strings
  // (emoji-free — canvas glyph support for emoji is unreliable), kept
  // separate so the painter stays dumb and the content stays greppable.
  const xp = miner.xp || {};
  return {
    title: miner.display_name,
    subtitle: `suid ${miner.suid ?? "unknown"}`,
    stats: [
      `Depth ${miner.depth}/${world?.max_depth ?? "?"} — ` +
        `${biomeName(miner.depth, world?.biomes)}` +
        ` · record depth ${miner.record_depth}`,
      `Level ${xp.level ?? "?"} · ${groupDigits(xp.game_total ?? 0)} ${xp.game ?? "?"} XP · ` +
        `${groupDigits(miner.coins ?? 0)} coins`,
    ],
    gear: shareCardGearLines(miner.gear),
    footer: "Mineverse — read-only mining economy viewer",
  };
}

function drawShareCardGem(ctx, x, y, size, color) {
  // Same gem geometry as oreIconSVG (diamond polygon + white glint),
  // scaled from that icon's 10×10 viewBox onto the canvas.
  const s = size / 10;
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.moveTo(x + 5 * s, y + 0.5 * s);
  ctx.lineTo(x + 9.5 * s, y + 4 * s);
  ctx.lineTo(x + 5 * s, y + 9.5 * s);
  ctx.lineTo(x + 0.5 * s, y + 4 * s);
  ctx.closePath();
  ctx.fill();
  ctx.fillStyle = "rgba(255, 255, 255, 0.25)";
  ctx.beginPath();
  ctx.moveTo(x + 5 * s, y + 0.5 * s);
  ctx.lineTo(x + 9.5 * s, y + 4 * s);
  ctx.lineTo(x + 5 * s, y + 4 * s);
  ctx.closePath();
  ctx.fill();
}

function drawShareCard(canvas, miner, world) {
  const t = SHARE_CARD_THEME;
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;
  const lines = shareCardLines(miner, world);
  // Backdrop: the page's "deeper is darker" gradient, one static frame.
  const backdrop = ctx.createLinearGradient(0, 0, 0, h);
  backdrop.addColorStop(0, t.bgTop);
  backdrop.addColorStop(1, t.bgBottom);
  ctx.fillStyle = backdrop;
  ctx.fillRect(0, 0, w, h);
  // Panel with the cave edge, like every .card on the page.
  ctx.fillStyle = t.panel;
  ctx.fillRect(16, 16, w - 32, h - 32);
  ctx.strokeStyle = t.edge;
  ctx.lineWidth = 2;
  ctx.strokeRect(16, 16, w - 32, h - 32);
  // Title (accent, like .card h3) + the suid identity line.
  ctx.fillStyle = t.accent;
  ctx.font = "bold 30px system-ui, sans-serif";
  ctx.fillText(lines.title, 40, 64);
  ctx.fillStyle = t.muted;
  ctx.font = "13px system-ui, sans-serif";
  ctx.fillText(lines.subtitle, 40, 86);
  // Headline stats.
  ctx.fillStyle = t.text;
  ctx.font = "17px system-ui, sans-serif";
  lines.stats.forEach((line, i) => ctx.fillText(line, 40, 126 + i * 28));
  // Key gear.
  ctx.fillStyle = t.muted;
  ctx.font = "bold 12px system-ui, sans-serif";
  ctx.fillText("KEY GEAR", 40, 204);
  ctx.fillStyle = t.text;
  ctx.font = "15px system-ui, sans-serif";
  const gearLines = lines.gear.length ? lines.gear : ["(no gear equipped)"];
  gearLines.forEach((line, i) => ctx.fillText(line, 40, 228 + i * 22));
  // Ore-tier gem flourish, stone → diamond, bottom right.
  const tiers = Object.entries(ORE_TIER_COLORS);
  tiers.forEach(([, color], i) => {
    drawShareCardGem(ctx, w - 44 - (tiers.length - i) * 30, h - 72, 22, color);
  });
  // Footer.
  ctx.fillStyle = t.muted;
  ctx.font = "12px system-ui, sans-serif";
  ctx.fillText(lines.footer, 40, h - 42);
}

function shareCardFileName(miner) {
  const base = String(miner.display_name || "miner")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return `mineverse-${base || "miner"}-card.png`;
}

function downloadCanvasPNG(canvas, fileName) {
  const save = (href, revoke) => {
    const link = document.createElement("a");
    link.href = href;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    link.remove();
    if (revoke) URL.revokeObjectURL(href);
  };
  if (typeof canvas.toBlob === "function") {
    canvas.toBlob((blob) => {
      if (blob) save(URL.createObjectURL(blob), true);
      else save(canvas.toDataURL("image/png"), false); // rare toBlob failure
    }, "image/png");
  } else {
    save(canvas.toDataURL("image/png"), false); // older browsers
  }
}

function shareCardButton(miner, world) {
  // Real <button> → keyboard-activatable + focus-visible for free. The
  // aria-label starts with the visible text (label-in-name) and says
  // honestly what happens: a PNG image gets downloaded.
  const button = el("button", "share-button", "Download card (PNG)");
  button.type = "button";
  button.setAttribute("aria-label",
    `Download card (PNG) — save ${miner.display_name}'s miner card ` +
    "as a PNG image");
  button.addEventListener("click", () => {
    const canvas = document.createElement("canvas"); // offscreen, never in DOM
    canvas.width = SHARE_CARD_WIDTH;
    canvas.height = SHARE_CARD_HEIGHT;
    drawShareCard(canvas, miner, world);
    downloadCanvasPNG(canvas, shareCardFileName(miner));
  });
  return button;
}

function renderMinerCard(miner, world, staleness) {
  const card = el("article", "card");
  const title = el("h3", null, miner.display_name);
  if (snapshotIsStale(staleness)) {
    // Stale snapshot → as far as the data shows, this miner is idle.
    // 💤 is decoration; the visually-hidden "(idle)" is the semantics.
    title.appendChild(decorative(el("span", "idle-mark", " 💤")));
    title.appendChild(visuallyHidden("span", " (idle)"));
  }
  card.appendChild(title);
  // Subtle identity line: the superbot user id (suid) the card is keyed
  // on — snapshot data shown verbatim, also serves the my-miner view.
  card.appendChild(el("p", "identity-line", `suid ${miner.suid ?? "unknown"}`));
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
      // xp.game names which game the XP belongs to (contract field, "?"
      // when absent) — no more hardcoded "mining" label.
      `Level ${xp.level ?? "?"} · ${groupDigits(xp.game_total ?? 0)} ${xp.game ?? "?"} XP · ` +
      `${groupDigits(miner.coins ?? 0)} 🪙`),
  );
  card.appendChild(energyMeter(miner.energy));
  section(card, "Gear", gearList(miner.gear, miner.suid));
  section(card, "Pack", groupedItemList(miner.pack));
  section(card, "Skills",
    rankedList(miner.skills, (name, rank) => `${name} · rank ${rank}`));
  section(card, "Structures",
    rankedList(miner.structures, (name, count) => `${count}× ${name}`));
  const vault = miner.vault || {};
  const vaultLevel = vault.level ?? 0;
  const vaultLevelMax = vault.level_max ?? 0;
  const vaultTitle = el("h4", null, `Vault · level ${vaultLevel} `);
  // Chest fill + pips both repeat the level graphically — decorative;
  // the visually-hidden line is the AT-facing "level N of M" equivalent.
  vaultTitle.appendChild(
    svgSpan("vault-chest", vaultChestSVG(vaultLevel, vaultLevelMax)));
  vaultTitle.appendChild(decorative(
    el("span", "vault-pips", ` ${vaultTierPips(vaultLevel, vaultLevelMax)}`)));
  vaultTitle.appendChild(
    visuallyHidden("span", ` vault level ${vaultLevel} of ${vaultLevelMax}`));
  card.appendChild(vaultTitle);
  groupedItemList(vault).forEach((n) => card.appendChild(n));
  card.appendChild(shareCardButton(miner, world));
  return card;
}

/* --- depth race (relative bar view, kept alongside the ladder) ---------- */

function renderDepthRace(miners, world) {
  const race = document.getElementById("depth-race");
  race.replaceChildren();
  for (const miner of [...miners].sort((a, b) => b.depth - a.depth)) {
    const row = el("div", "race-row");
    row.appendChild(el("span", "race-name", miner.display_name));
    // The bar is a graphical repeat of the depth — decorative; the
    // visually-hidden line carries the same info for screen readers.
    const track = decorative(el("div", "race-track"));
    const bar = el("div", "race-bar");
    bar.style.width =
      `${world.max_depth ? (miner.depth / world.max_depth) * 100 : 0}%`;
    track.appendChild(bar);
    row.appendChild(track);
    row.appendChild(
      visuallyHidden("span", `depth ${miner.depth} of ${world.max_depth}, `));
    row.appendChild(el("span", "race-depth", biomeLabel(miner.depth, world.biomes)));
    race.appendChild(row);
  }
}

/* --- depth/biome ladder (bands 0–3, current + record markers) ----------- */

function bandTintClass(depth) {
  // Biome tint hook (band-depth-0..3, style.css); deeper-than-known
  // bands clamp to the deepest tint instead of losing their theming.
  return `band-depth-${Math.max(0, Math.min(depth, 3))}`;
}

function renderLadder(ladder, hats) {
  // Side-view mine shaft: stacked biome-tinted strata (CSS layers the
  // dirt-lip → stone → biome gradients per band-depth class); miner
  // avatars, their cosmetic hats and record flags are aria-hidden
  // decoration ON the chips — the chip text ("Name", "Name · record")
  // stays the semantics, and the hat gets a visually-hidden text
  // alternative carrying its label (the a11y pattern everywhere else).
  const holder = document.getElementById("depth-ladder");
  holder.replaceChildren();
  const hatFor = hatsByName(hats);
  for (const band of ladder || []) {
    const row = el("div", `ladder-band ${bandTintClass(band.depth)}`);
    row.appendChild(bandLabel(band.depth, band.biome));
    const chips = el("div", "ladder-chips");
    for (const name of band.here) {
      const chip = el("span", "chip");
      const hat = hatFor[name];
      chip.appendChild(svgSpan("miner-avatar", minerAvatarSVG(hat)));
      chip.appendChild(document.createTextNode(name));
      if (hat) {
        chip.appendChild(
          visuallyHidden("span", `, wearing a ${hat.label}`));
      }
      chips.appendChild(chip);
    }
    for (const name of band.record_only) {
      const chip = el("span", "chip record");
      chip.appendChild(svgSpan("record-flag", recordFlagSVG()));
      chip.appendChild(document.createTextNode(`${name} · record`));
      chips.appendChild(chip);
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
    // point.names lists EVERY miner in this cell (server-grouped) — one
    // dot per occupied cell, so co-located miners can't overlap unseen.
    const who = point.names.join(", ");
    const dot = el("span", "minimap-point");
    dot.style.left =
      `${(((point.x - panel.bounds.min_x) + MINIMAP_PAD) / spanX) * 100}%`;
    dot.style.top =
      `${(((point.y - panel.bounds.min_y) + MINIMAP_PAD) / spanY) * 100}%`;
    dot.title = `${who} at (${point.x}, ${point.y})`;
    if (point.names.length > 1) {
      dot.appendChild(
        el("span", "minimap-count", `×${point.names.length}`));
    }
    dot.appendChild(
      el("span", "minimap-name", `${who} (${point.x}, ${point.y})`));
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
    const band = el("div", `minimap-band ${bandTintClass(panel.depth)}`);
    band.appendChild(bandLabel(panel.depth, panel.biome));
    const body = el("div", "minimap-body");
    if (panel.bounds) {
      // The 2-D plot is decorative for assistive tech; the
      // visually-hidden list below conveys the same positions as text.
      body.appendChild(decorative(minimapPlot(panel)));
      const alt = visuallyHidden("ul");
      for (const point of points) {
        // Every co-located name lands in the text alternative too.
        alt.appendChild(
          el("li", null,
            `${point.names.join(", ")} at (${point.x}, ${point.y})`));
      }
      body.appendChild(alt);
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

const MEDALS = ["🥇", "🥈", "🥉"]; // podium marks, decorative (rank stays text)

function countUpCell(cell, value) {
  // Count a numeric cell up to the server value. ALWAYS ends by writing
  // the exact final value (no drift), and renders instantly when the
  // value isn't a plain number or the user prefers reduced motion.
  const finalText = groupDigits(value);
  if (typeof value !== "number" || !Number.isFinite(value) ||
      prefersReducedMotion() ||
      typeof requestAnimationFrame !== "function") {
    cell.textContent = finalText;
    return;
  }
  const duration = 600; // ms — short enough to never lag a tab switch
  const start = performance.now();
  const step = (now) => {
    const t = Math.min((now - start) / duration, 1);
    if (t >= 1) {
      cell.textContent = finalText; // exact final value — no drift
      return;
    }
    cell.textContent = groupDigits(Math.round(value * t));
    requestAnimationFrame(step);
  };
  cell.textContent = "0";
  requestAnimationFrame(step);
}

function renderBoard(board) {
  const table = document.getElementById("leaderboard");
  const thead = table.querySelector("thead");
  const tbody = table.querySelector("tbody");
  thead.replaceChildren();
  tbody.replaceChildren();
  thead.appendChild(tableHeadRow(["#", "Miner", ...(board?.columns || [])]));
  (board?.rows || []).forEach((row, rank) => {
    const tr = el("tr", rank < MEDALS.length ? `podium podium-${rank + 1}` : null);
    row.forEach((cell, i) => {
      const td = el("td");
      if (i === 0 && rank < MEDALS.length) {
        // Medal is decorative; the rank NUMBER stays in the cell text.
        td.appendChild(decorative(el("span", "medal", `${MEDALS[rank]} `)));
        td.appendChild(document.createTextNode(String(cell)));
      } else if (i >= 2) {
        countUpCell(td, cell); // score columns count up to the exact value
      } else {
        td.textContent = String(cell);
      }
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
}

function renderBoardTabs(leaderboards) {
  // WAI-ARIA tabs: role=tablist lives on the static #board-tabs holder
  // (web/index.html); each button is a role=tab controlling the one
  // #leaderboard-panel. Roving tabindex + arrow keys move between tabs.
  const tabs = document.getElementById("board-tabs");
  const panel = document.getElementById("leaderboard-panel");
  const caption = document.getElementById("leaderboard-caption");
  tabs.replaceChildren();
  let active = BOARD_TABS[0][0];
  const buttons = new Map();
  const select = (key, focus) => {
    active = key;
    let activeLabel = key;
    for (const [k, label] of BOARD_TABS) if (k === key) activeLabel = label;
    for (const [k, b] of buttons) {
      const selected = k === active;
      b.classList.toggle("active", selected);
      b.setAttribute("aria-selected", String(selected));
      b.tabIndex = selected ? 0 : -1; // roving tabindex
    }
    panel.setAttribute("aria-labelledby", `board-tab-${active}`);
    caption.textContent = `Leaderboard — miners ranked by ${activeLabel}`;
    renderBoard(leaderboards?.[active]);
    if (focus) buttons.get(active).focus();
  };
  const keys = BOARD_TABS.map(([key]) => key);
  const onTabKeydown = (event) => {
    const idx = keys.indexOf(active);
    let next = null;
    if (event.key === "ArrowRight") next = keys[(idx + 1) % keys.length];
    else if (event.key === "ArrowLeft") {
      next = keys[(idx - 1 + keys.length) % keys.length];
    } else if (event.key === "Home") next = keys[0];
    else if (event.key === "End") next = keys[keys.length - 1];
    if (next !== null) {
      event.preventDefault();
      select(next, true);
    }
  };
  for (const [key, label] of BOARD_TABS) {
    const button = el("button", "board-tab", label);
    button.type = "button";
    button.id = `board-tab-${key}`;
    button.setAttribute("role", "tab");
    button.setAttribute("aria-controls", "leaderboard-panel");
    button.addEventListener("click", () => select(key));
    button.addEventListener("keydown", onTabKeydown);
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
  table.appendChild(visuallyHidden(
    "caption",
    "Inventory browser — quantity of each item carried, per miner"));
  const thead = el("thead");
  thead.appendChild(tableHeadRow(["Item", "Total", ...matrix.columns]));
  table.appendChild(thead);
  const tbody = el("tbody");
  for (const row of matrix.rows) {
    const tr = el("tr");
    row.forEach((cell, i) => {
      // First column is the row header (the item name).
      const tag = i === 0 ? "th" : "td";
      const node = el(tag);
      if (i === 0) {
        // Ore tiers get their rarity icon + tint; the item NAME stays
        // the header text (unknown items simply get no icon).
        const icon = oreIconSVG(cell);
        node.className = icon ? `item-name tier-${cell}` : "item-name";
        if (icon) node.appendChild(svgSpan("ore-icon", icon));
        node.appendChild(document.createTextNode(String(cell)));
        node.scope = "row";
      } else {
        node.textContent = i >= 2 && cell === 0 ? "·" : String(cell);
      }
      if (i === 1) node.className = "item-total";
      tr.appendChild(node);
    });
    tbody.appendChild(tr);
  }
  table.appendChild(tbody);
  holder.appendChild(table);
}

/* --- achievements (server-derived: /api/views `achievements`) -------------
 * server/views.py build_achievements does ALL the math (pytest-covered);
 * this only paints badges. Emoji are aria-hidden decoration — the badge
 * NAME is always the text. Zero badges renders an honest empty state. */

function achievementBadge(entry) {
  const badge = el("li", "badge-chip");
  badge.title = entry.description;
  badge.appendChild(decorative(el("span", "badge-emoji", `${entry.emoji} `)));
  badge.appendChild(document.createTextNode(entry.name));
  return badge;
}

function renderAchievements(achievements) {
  const rollup = document.getElementById("achievements-rollup");
  const holder = document.getElementById("achievements-miners");
  rollup.replaceChildren();
  holder.replaceChildren();
  const catalog = achievements?.catalog || [];
  const miners = achievements?.miners || [];
  if (!catalog.length) {
    rollup.appendChild(el("p", "empty",
      "(no achievement catalog in this snapshot view)"));
    return;
  }
  const byId = new Map(catalog.map((entry) => [entry.id, entry]));
  // Roll-up: every achievement with its earners listed honestly —
  // including "nobody yet" (e.g. Fully Geared / Tool Breaker today).
  const list = el("ul", "items rollup-list");
  for (const entry of catalog) {
    const li = el("li", "rollup-entry");
    li.appendChild(decorative(el("span", "badge-emoji", `${entry.emoji} `)));
    li.appendChild(el("strong", null, entry.name));
    li.appendChild(el("span", "rollup-desc", ` — ${entry.description}`));
    const earners = miners
      .filter((m) => (m.earned || []).includes(entry.id))
      .map((m) => m.display_name);
    li.appendChild(el("span", "rollup-earners",
      earners.length ? ` · ${earners.join(", ")}` : " · nobody yet"));
    list.appendChild(li);
  }
  rollup.appendChild(list);
  // Per-miner badge cards.
  for (const m of miners) {
    const card = el("article", "card achievement-card");
    card.appendChild(el("h3", null, m.display_name));
    const earned = (m.earned || []).map((id) => byId.get(id)).filter(Boolean);
    if (!earned.length) {
      card.appendChild(el("p", "empty", "(no achievements yet)"));
    } else {
      const badges = el("ul", "badge-list");
      earned.forEach((entry) => badges.appendChild(achievementBadge(entry)));
      card.appendChild(badges);
    }
    holder.appendChild(card);
  }
  if (!miners.length) {
    holder.appendChild(el("p", "empty", "(no miners in this snapshot)"));
  }
}

/* --- miner VS (side-by-side comparison, native selects) ------------------- */

function packTotal(pack) {
  // Total item count carried: every entry of the shaped pack, ores +
  // other. Non-numeric counts (schema-forbidden) simply don't add.
  const entries = [...(pack?.ores || []), ...(pack?.other || [])];
  return entries.reduce(
    (sum, [, qty]) => sum + (typeof qty === "number" ? qty : 0), 0);
}

function skillRankTotal(skills) {
  // Sum of all skill ranks — one number for the comparison table.
  return (Array.isArray(skills) ? skills : []).reduce(
    (sum, [, rank]) => sum + (typeof rank === "number" ? rank : 0), 0);
}

// Stat rows for the VS table: label + reader over a SHAPED miner
// (server/views.py shape_miner). Missing values read as 0 — the shaped
// miner already defaults these fields server-side.
const VS_STATS = [
  ["depth", (m) => m.depth ?? 0],
  ["record depth", (m) => m.record_depth ?? 0],
  ["level", (m) => m.xp?.level ?? 0],
  ["mining XP", (m) => m.xp?.game_total ?? 0],
  ["coins", (m) => m.coins ?? 0],
  ["energy", (m) => m.energy?.current ?? 0],
  ["vault level", (m) => m.vault?.level ?? 0],
  ["pack total", (m) => packTotal(m.pack)],
  ["skill ranks", (m) => skillRankTotal(m.skills)],
];

function vsValueCell(value, other) {
  // The real value is plain text; the bar (scaled against the larger of
  // the pair) is aria-hidden decoration on top of it.
  const td = el("td", value > other ? "vs-lead" : null);
  td.appendChild(el("span", "vs-value", groupDigits(value)));
  const track = decorative(el("span", "vs-track"));
  const bar = el("span", "vs-bar");
  const peak = Math.max(value, other, 1);
  bar.style.width = `${(Math.max(value, 0) / peak) * 100}%`;
  track.appendChild(bar);
  td.appendChild(track);
  return td;
}

function renderVsComparison(a, b) {
  const holder = document.getElementById("vs-compare");
  holder.replaceChildren();
  if (!a || !b) {
    holder.appendChild(el("p", "empty",
      "Pick two miners above to compare them."));
    return;
  }
  if (a.suid === b.suid) {
    holder.appendChild(el("p", "empty",
      "That is the same miner twice — a miner always ties with themself. " +
      "Pick two different miners."));
    return;
  }
  const table = el("table", "vs-table");
  table.appendChild(visuallyHidden("caption",
    `Miner VS — ${a.display_name} versus ${b.display_name}, stat by stat`));
  const thead = el("thead");
  thead.appendChild(tableHeadRow(["Stat", a.display_name, b.display_name]));
  table.appendChild(thead);
  const tbody = el("tbody");
  for (const [label, read] of VS_STATS) {
    const tr = el("tr");
    const th = el("th", null, label);
    th.scope = "row";
    tr.appendChild(th);
    const va = read(a);
    const vb = read(b);
    tr.appendChild(vsValueCell(va, vb));
    tr.appendChild(vsValueCell(vb, va));
    tbody.appendChild(tr);
  }
  table.appendChild(tbody);
  holder.appendChild(table);
}

function renderVs(miners) {
  const selectA = document.getElementById("vs-a");
  const selectB = document.getElementById("vs-b");
  const bySuid = new Map(miners.map((m) => [String(m.suid), m]));
  for (const select of [selectA, selectB]) {
    select.replaceChildren();
    const none = document.createElement("option");
    none.value = "";
    none.textContent = "— pick a miner —";
    select.appendChild(none);
    for (const m of miners) {
      const option = document.createElement("option");
      option.value = String(m.suid);
      option.textContent = m.display_name;
      select.appendChild(option);
    }
  }
  const repaint = () => renderVsComparison(
    bySuid.get(selectA.value) || null, bySuid.get(selectB.value) || null);
  selectA.addEventListener("change", repaint);
  selectB.addEventListener("change", repaint);
  repaint(); // honest "pick two miners" state before any choice
}

/* --- top-level render ------------------------------------------------------ */

function render(views) {
  // /api/views is the snapshot (READ contract v1) shaped server-side —
  // schema_version/generated_at pass through for the meta line.
  const meta = document.getElementById("snapshot-meta");
  meta.textContent =
    `snapshot v${views.schema_version ?? "?"} · ` +
    `generated ${views.generated_at || "unknown"} · ` +
    `guild ${views.guild_id || "unknown"}`;
  renderStaleness(views.staleness);

  const miners = views.miners || [];
  if (!miners.length) {
    showBanner("Snapshot loaded, but it contains no miners.", false);
    return;
  }

  renderLadder(views.ladder, views.hats);
  renderDepthRace(miners, views.world);
  renderMinimap(views.minimap);
  renderBoardTabs(views.leaderboards);
  renderInventory(views.inventory);
  renderAchievements(views.achievements);
  renderVs(miners);
  const cards = document.getElementById("miner-cards");
  cards.replaceChildren();
  miners.forEach((m) =>
    cards.appendChild(renderMinerCard(m, views.world, views.staleness)));

  for (const id of ["depth-ladder-section", "depth-race-section",
                    "minimap-section", "leaderboard-section",
                    "inventory-browser-section", "achievements-section",
                    "vs-section", "miners-section"]) {
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
    holder.replaceChildren(
      renderMinerCard(shaped, views.world, views.staleness));
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

function retryAfterText(headerValue) {
  // Retry-After on a 429 is integer seconds (write contract § Rate
  // limits) and the relay never invents one — so anything absent or
  // non-integer means no hint, never a guess. Pure: string|null in,
  // suffix (or "") out.
  if (typeof headerValue !== "string" || !/^\d+$/.test(headerValue.trim())) {
    return "";
  }
  const seconds = Number(headerValue.trim());
  return seconds > 0 ? ` — retry in ${seconds}s` : "";
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
      // On 429 the relay forwards the executor's Retry-After header
      // (integer seconds — same-origin fetch, so readable directly);
      // when it parses, the rejection line gains the backoff hint.
      const hint = res.status === 429
        ? retryAfterText(res.headers.get("Retry-After"))
        : "";
      showActionResult(`✗ ${data.reason_code}: ${data.message}${hint}`, true);
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

function numberInput(placeholder, ariaLabel) {
  const input = document.createElement("input");
  input.type = "number";
  input.min = "1";
  input.placeholder = placeholder;
  input.className = "action-input";
  // A placeholder is not an accessible name (WCAG 4.1.2): name the control
  // for screen readers when a label is supplied, without disturbing layout.
  if (ariaLabel) input.setAttribute("aria-label", ariaLabel);
  return input;
}

function textInput(placeholder, ariaLabel) {
  const input = document.createElement("input");
  input.type = "text";
  input.placeholder = placeholder;
  input.className = "action-input";
  // A placeholder is not an accessible name (WCAG 4.1.2): name the control
  // for screen readers when a label is supplied, without disturbing layout.
  if (ariaLabel) input.setAttribute("aria-label", ariaLabel);
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
  const sellItem = textInput("item (e.g. stone)", "Item to sell");
  const sellQty = numberInput("qty", "Quantity to sell");
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
  const vaultAmount = numberInput("coins", "Vault amount");
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
  const equipItem = textInput("item (e.g. iron pickaxe)", "Item to equip");
  const equipSlot = document.createElement("select");
  equipSlot.className = "action-input";
  equipSlot.setAttribute("aria-label", "Equipment slot");
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
  console.log(CONSOLE_GREETING); // a hello for whoever opens the shaft
  // Seasonal decor: the real current date enters HERE, once, as the
  // viewer's LOCAL calendar date (decorations follow the wall calendar,
  // not UTC) — everything downstream is pure and date-injected.
  const today = new Date();
  applySeasonalDecor([
    today.getFullYear(),
    String(today.getMonth() + 1).padStart(2, "0"),
    String(today.getDate()).padStart(2, "0"),
  ].join("-"));
  let views = null;
  // Until the snapshot resolves the page is header-only (every section
  // ships hidden), so say what's happening through the same banner the
  // error path uses.
  showBanner("Loading snapshot…", false);
  try {
    const res = await fetch("/api/views");
    if (!res.ok) throw new Error(`API responded ${res.status}`);
    views = await res.json();
    // Clear the loading line BEFORE render — render() raises its own
    // banner for an empty snapshot, and that one must stay up.
    hideBanner();
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
