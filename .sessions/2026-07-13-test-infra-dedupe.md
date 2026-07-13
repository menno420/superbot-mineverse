# Session — 2026-07-13 — test-infra dedupe + views schema loader (self-initiated)

> **Status:** `in-progress`
> **Branch:** `claude/test-infra-dedupe`
> **Venue:** lane worker session (ORDER 004 night run — generative rung:
> self-initiated, contained, reversible).

**Goal:** harvest two more recorded 💡 ideas from this lane's own session
cards — both genuine entries, now acted on:

1. **Served-bytes fixture dedupe into `tests/conftest.py`** (idea from
   `2026-07-12-webaudio-cave-toggle`): six web test modules
   (test_web_a11y, test_web_audio, test_web_fun, test_web_seasonal,
   test_web_share_card, test_web_visuals) carry a byte-identical copied
   fixture stack — module-scoped `base_url` (one real `make_server` per
   module), the `fetch_text` helper, and the `html`/`js`/`css` text
   fixtures. Move the genuinely-identical stack into a new
   `tests/conftest.py` (module scope PRESERVED — still one server per
   module, no cross-module sharing surprise); leave module-specific
   variants (`not_found_page` in test_web_fun, `seasonal_js_block` in
   test_web_seasonal) where they are. Zero behavior change; the whole
   suite must stay at exactly **522 passed + 1 skipped**.
2. **`views.py` third schema parse → shared cached loader** (idea from
   `2026-07-13-server-internals-dedupe`, cited at views.py:26-28):
   `server/views.py` keeps its own `SCHEMA_PATH` + module-level
   `_SCHEMA = json.loads(...)` just to derive `_MINER_PROPS`. Point it at
   the now-cached `snapshot_validation.load_schema()` (lru_cache, landed
   in PR #62) — one schema, one parse, one path constant. Precondition
   verified before switching: same file, same `json.loads`-of-read_text
   parse, and views is strictly read-only over the dict (every consumer
   wraps in `list(...)` or returns a scalar), so sharing the cached dict
   introduces no mutation hazard. Mind the dual-import dance
   (`try: from server import … except ImportError`) app.py and
   response_validation.py use for direct-script runs.

Dedupe, not redesign: diff stays mechanical. Baseline at base
(main @ bf93786, carrying #60/#61/#62): **522 passed + 1 skipped**.

- **📊 Model:** fable-5 · standard effort · task-class: self-initiated test-infra dedupe — shared served-bytes fixtures + views on cached schema loader (refactor)
