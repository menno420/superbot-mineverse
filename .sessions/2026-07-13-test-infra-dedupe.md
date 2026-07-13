# Session — 2026-07-13 — test-infra dedupe + views schema loader (self-initiated)

> **Status:** `complete`
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

## Close-out

Shipped on `claude/test-infra-dedupe` (base: main @ bf93786). Both
halves landed; no scope cut.

**The conftest, exactly the recorded recipe:** `tests/conftest.py` (new,
one honest docstring + the stack verbatim) now owns the module-scoped
`base_url` fixture, the `fetch_text` helper and the `html`/`js`/`css`
text fixtures; the six copies deleted mechanically (each stanza matched
as an exact byte string and asserted to occur exactly once before
replacement — no regex creativity). Scope stayed `module`, NOT
`session`: each web module still gets its own server, so the move is
provably behavior-free rather than a quiet perf "improvement" bundled
in. Module-specific fixtures stayed put (`not_found_page` in
test_web_fun.py, which keeps its own `pytest`/`urllib` imports;
`seasonal_js_block` in test_web_seasonal.py). Web-suite collection
pinned identical before/after: **81 collected** both sides. Net −176
lines across the diff.

**The views switch, precondition verified first:** confirmed
`views._SCHEMA` was the same file (`schemas/mining_snapshot.v1.
schema.json`) parsed the same way (`json.loads` of `read_text`) as
`snapshot_validation.load_schema()`, and that views is strictly
read-only over the dict — every consumer is a `list(...)` copy or a
scalar lookup, and nothing outside the module references
`views.SCHEMA_PATH`/`views._SCHEMA` (grepped tests/, server/,
scripts/). So no deepcopy boundary needed; the mutation hazard the
task flagged does not arise, and the module docstring now states the
shared-cached-instance rule so a future writer trips over it in
prose before they trip over it in prod. The dual-import dance
(`try: from server import … except ImportError`) copied verbatim from
response_validation.py; both import paths exercised
(`python3 -c` package-style AND with `server/` on sys.path). The
test-side mirror at tests/test_views.py:28-30 stays, as the source
idea prescribed — it is the independent witness the wiring tests
compare against. views.py's `json`/`Path` imports and
`REPO_ROOT`/`SCHEMA_PATH` constants existed ONLY for the private
parse, so they left with it (ruff clean).

Suite: **522 passed + 1 skipped** — baseline-identical, as a pure
dedupe must be; `bootstrap.py check --strict` green at this flip.
Files: `tests/conftest.py` (new), `tests/test_web_a11y.py`,
`tests/test_web_audio.py`, `tests/test_web_fun.py`,
`tests/test_web_seasonal.py`, `tests/test_web_share_card.py`,
`tests/test_web_visuals.py`, `server/views.py`, plus records.

One pre-existing nit seen and left (out of scope, one line to fix):
`tests/test_snapshot_validation.py:14` imports `http.client` unused
(ruff F401) — trivially fixable by whichever session next touches that
file.

## 💡 Session idea

The same copied-stack disease exists one shelf over: SIX non-web suites
each define a private `serve()` contextmanager around
`make_server(port=0, **kwargs)` + daemon thread + shutdown
(tests/test_actions.py:153, test_api.py:24, test_auth.py:46,
test_server_robustness.py:31, test_snapshot_validation.py:214,
test_views.py:545). Unlike the web fixtures these take PER-TEST kwargs
(snapshot_path, write config…), so a pytest fixture is the wrong shape —
the shared form is a plain kwargs-taking context manager in an
importable helper module (e.g. `tests/_server_helpers.py`; conftest.py
is pytest-magic, not an import target). Guard recipe: move ONE
canonical `serve()` there, point the six copies at it (some wrap extra
locals — keep those wrappers, dedupe only the identical core), verified
by the whole suite staying at 522 passed + 1 skip.

## ⟲ Previous-session review

The `2026-07-13-server-internals-dedupe` card set this session up to be
cheap, which is what a good refactor card does: its 💡 guard recipe was
followed step-for-step and every warning in it turned out load-bearing —
the dual-import dance it flagged was exactly the snag to avoid, and the
"test-side mirror can stay" call saved a wrong deletion. Its cache
close-out sentence "a caller mutating [the cached dict] would be a new
bug class — acceptable because every consumer is read-only today" did
real work tonight: this session ADDED a consumer (views), and that
sentence is why the mutation audit happened BEFORE the switch rather
than after a prod surprise — the read-only rule is now restated in
views.py's own docstring so the invariant travels with the code. Honest
size-claim discipline held (its "net −24 lines in the four handlers"
checks out against the diff). The seven-review-old records-pass nit it
escalated to "next records/closeout session must land it or drop it in
one line" stands unchanged — this is a code slice, not a records
session, so the escalation transfers as-is, un-softened.

- **📊 Model:** fable-5 · standard effort · task-class: self-initiated test-infra dedupe — shared served-bytes fixtures + views on cached schema loader (refactor)
