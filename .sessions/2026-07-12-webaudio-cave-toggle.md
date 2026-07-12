# Session — 2026-07-12 — WebAudio ambient cave toggle (backlog item 5)

> **Status:** `in-progress`
> **Branch:** `claude/webaudio-cave-toggle`
> **Venue:** lane worker session (coordinator-delegated groomed-backlog slice).

**Goal:** ship groomed-backlog item 5
(`docs/ideas/founding-day-groomed-backlog-2026-07-11.md`): ambient cave
audio, muted by default, honest toggle. No audio asset files — the
ambience is SYNTHESIZED with the WebAudio API (looped low-pass-filtered
noise for cave wind + occasional soft sine "drips" on a decay envelope),
kept whisper-quiet. MUTED BY DEFAULT, always: the AudioContext is created
only inside the toggle button's click handler — no sound can exist before
an explicit opt-in (no-autoplay discipline; the browser gesture
requirement agrees). The toggle is a REAL button reflecting true state
(`aria-pressed` + visible "🔇 Cave sounds off" / "🔊 Cave sounds on"
label, keyboard-activatable for free, cave-theme styled); state does NOT
persist across reloads — nothing in web/ persists UI state (no
localStorage anywhere), so this follows suit. Nothing on the page pulses
or animates with the audio, so `prefers-reduced-motion` needs no new
gate — the toggle stays available and the single `prefersReducedMotion()`
/ matchMedia path stays single. Decision logic stays PURE functions
pinned per-CI-run via the PR #48 `js_call` harness (audio-graph spec from
config, deterministic drip-delay scatter, toggle-state/label); the
impure WebAudio wiring is a thin interpreter of the pure spec. JSON API
byte-identical; no new endpoints; no npm/package.json.
