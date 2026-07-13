# Session — 2026-07-13 — server internals dedupe (self-initiated)

> **Status:** `complete`
> **Branch:** `claude/server-internals-dedupe`
> **Venue:** lane worker session (ORDER 004 night run — generative rung:
> self-initiated, contained, reversible).

**Goal:** land the two refactor ideas recorded by tonight's own session
cards — both genuine 💡 entries, now acted on:

1. **`_load_valid_snapshot` helper** (idea from
   `2026-07-13-snapshot-ingestion-seam`): `server/app.py` repeats the same
   load-validate-or-503 block at all four snapshot load paths
   (`_serve_snapshot`, `_serve_views`, `_serve_me`, `_serve_action`
   pre-relay). Extract ONE
   `_load_valid_snapshot(self) -> tuple[bytes, dict] | None` helper
   (returns the raw payload too — `_serve_snapshot` ETags the exact
   bytes — and sends the honest 503 itself on failure); collapse the four
   sites onto it. Behavior byte-identical; the existing HTTP sections of
   `tests/test_snapshot_validation.py` and the malformed-snapshot tests in
   `tests/test_server_robustness.py` are the safety net.
2. **Cache the parsed schemas** (idea from
   `2026-07-13-write-path-hardening`): `functools.lru_cache` on the two
   `load_schema()` functions only (`server/snapshot_validation.py`,
   `server/response_validation.py`) — the schemas are COMMITTED files,
   immutable under a running server, unlike the live-fed snapshot which
   stays re-read fresh per request. `cache_clear()` is the explicit reload
   seam; add a small test per module pinning cache + seam, and the
   existing valid→valid→corrupt snapshot rewrite test must stay green.

Dedupe, not redesign: diff stays small and mechanical. Baseline at base
(PR #61 head 2f24b60): **520 passed + 1 skipped**.

## Close-out

Shipped on `claude/server-internals-dedupe` (base: PR #61's head 2f24b60 —
main @ 7f33c2b did not yet carry #60's `response_validation.py` or #61's
`conformance_run.py`; "based on #61" per the dependent-slice rule, noted
in the PR body). Both halves landed; neither turned out bigger than it
looked, so no scope cut.

**The helper, exactly the recorded recipe:**
`_load_valid_snapshot(self) -> tuple[bytes, dict] | None` in
`server/app.py` — reads `self.snapshot_path` fresh, parses, runs
`_snapshot_is_valid`, and on ANY failure (missing/unreadable file, invalid
JSON, v1 violation) sends the honest
`503 {"error": "snapshot unavailable"}` ITSELF and returns `None`, so a
call site is two lines and cannot forget one half. It returns the raw
bytes alongside the parsed dict because `_serve_snapshot` ETags and serves
the exact file bytes; the other three sites use the parsed half. All four
sites collapsed; net −24 lines in the four handlers. Zero new tests for
the helper by decision: it contains no logic the existing route-level
tests don't already pin from the outside (four routes × missing/corrupt/
invalid → 503, the ETag pins, the live-rewrite freshness pin) — a
helper-level test would only re-state them against a private method.

**The cache, on the ruler and never the measurement:**
`@lru_cache(maxsize=None)` on exactly the two `load_schema()` functions.
The distinction that makes this compatible with the statelessness doctrine
(and with the ingestion-seam card's declined last-good cache): the
SCHEMAS are committed files that cannot change under a running server —
the live-fed snapshot and the executor's response body are the things
being measured and stay re-read/judged fresh per request (the
valid→valid→corrupt rewrite test still green pins that). Each module's
docstring now records this; `response_validation`'s old "re-read per call,
honesty beats a cache" paragraph is rewritten rather than silently
contradicted. `cache_clear()` is the explicit reload seam, pinned by one
new test per module (cache hit is identity-same object; a schema-file edit
is invisible until `cache_clear()`, then genuinely picked up; path
restored + cache cleared in `finally` so no cross-test pollution). The
cached dict is shared, so a caller mutating it would be a new bug class —
acceptable because every consumer (`_check`, the jsonschema parity tests)
is read-only today.

Suite: **522 passed + 1 skipped** (baseline 520 + 1 at 2f24b60, +2 new
cache-seam tests); `bootstrap.py check --strict` green at this flip.
Files: `server/app.py`, `server/snapshot_validation.py`,
`server/response_validation.py`, `tests/test_snapshot_validation.py`,
`tests/test_response_validation.py`, plus records.

## 💡 Session idea

There is a THIRD independent parse of the snapshot schema at runtime:
`server/views.py:26-28` keeps its own `SCHEMA_PATH` + module-level
`_SCHEMA = json.loads(...)` just to read
`_SCHEMA["$defs"]["miner"]["properties"]` (the miner-field allowlist for
the inventory browser). Now that `snapshot_validation.load_schema()` is
cached, views.py could drop its private copy and derive `_MINER_PROPS`
from the shared loader — one schema, one parse, one path constant. Guard
recipe: replace `views.SCHEMA_PATH`/`views._SCHEMA` with
`snapshot_validation.load_schema()["$defs"]["miner"]["properties"]`
(watch the `try: from server import …` dual-import dance app.py/`
response_validation.py` use for direct-script runs), verified by
`tests/test_views.py` staying green — its own `_SCHEMA` copy at
`tests/test_views.py:28-30` is a test-side mirror and can stay.

## ⟲ Previous-session review

The `2026-07-13-conformance-runner` card is a tight tooling close-out:
every decide-and-flag bullet (derivation refusing to guess, the bounded
fingerprint deviation from `readiness_check.py`'s never-anything rule,
exit-code 4 deliberately unused so the wrapper can't masquerade as the
seam's abort) names both the decision AND the boundary it respects, and
the live three-path verification (pass/misconfigured/probe-fail) is the
right evidence for an operational wrapper. Its size-claim discipline nit
on the previous card ("~30 lines" vs the shipped file) was taken to heart
in this card's own numbers. Its 💡 `_envlib` idea (shared env-name
constants + a cross-module `ACTION_PATH` equality pin across
`conformance_run`/`shim_bot`/`readiness_check`) remains unlanded,
right-sized, and is the same dedupe-behind-one-seam class as tonight's
work — a natural next generative-rung slice. The records-pass nit
(bare-`📊 Model:` sweep on the 2026-07-12 cards) that card escalated to
"DECIDE, not re-carry" is now seven reviews old; this session, being a
code slice, re-carries it one last time with the same escalation: next
records/closeout session must land it or write the one line dropping it.

- **📊 Model:** fable-5 · standard effort · task-class: self-initiated server internals dedupe — snapshot load helper + schema-loader cache (refactor)
