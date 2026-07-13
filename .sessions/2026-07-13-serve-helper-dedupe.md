# Session — 2026-07-13 — serve() helper dedupe + unused-import nit (self-initiated)

> **Status:** `complete`
> **Branch:** `claude/serve-helper-dedupe`
> **Venue:** lane worker session (coordinator green-light wave — generative
> rung: self-initiated, contained, reversible).

**Goal:** harvest the recorded 💡 from
`.sessions/2026-07-13-test-infra-dedupe.md` plus the one-line nit that same
card left behind:

1. **serve() dedupe across the six non-web suites** (idea cited at
   tests/test_actions.py:153, test_api.py:24, test_auth.py:46,
   test_server_robustness.py:31, test_snapshot_validation.py:214,
   test_views.py:545): each suite carries a private kwargs-taking `serve()`
   around `make_server(port=0, **kwargs)` + daemon thread + shutdown. Extract
   ONE canonical importable helper and collapse the genuinely-identical
   copies onto it; leave genuinely-divergent variants alone with a stated
   reason.
2. **Unused-import nit**: `tests/test_snapshot_validation.py:14` imports
   `http.client` unused (ruff F401, pre-existing, flagged by the source
   card's close-out). Verify genuinely unused, then remove.

Zero behavior change; suite count must stay at the measured baseline
(main @ 3fe538e): **522 passed + 1 skipped**.

## Close-out

Shipped on `claude/serve-helper-dedupe` (base: main @ 3fe538e). Both
halves landed; no scope cut. Decide-and-flag: shape decisions below were
taken without a round-trip, flagged here and in the PR body.

**The helper, one correction to the recorded recipe:** the source card
called the six copies "contextmanagers" and declared "a pytest fixture is
the wrong shape" for per-test kwargs — inspected at HEAD, the copies were
already pytest FIXTURES, each yielding a kwargs-taking `_start(**kwargs)`
factory, so the fixture shape handles kwargs fine. What the recipe got
right is the importable core: `tests/_server_helpers.py` (new) now owns
`serve_factory()`, a plain `@contextmanager` yielding that factory
(ephemeral-port `make_server(port=0, **kwargs)` + daemon thread; every
started server shut down on exit — `try/finally`, identical teardown
order). `tests/conftest.py` wraps it in ONE per-test-scoped `serve`
fixture, and the five byte-identical copies were deleted outright
(test_actions.py, test_api.py, test_auth.py, test_snapshot_validation.py,
test_views.py — each left a one-line pointer comment). Scope stayed
per-test, exactly as the five copies were; the `tests.` package import
pattern was already proven in-tree (test_actions.py imports
`tests.shim.shim_bot`).

**Left alone, and why:** `tests/test_server_robustness.py`'s `serve` is
genuinely divergent — its `_start` returns the raw `(host, port)` tuple
for http.client round-trips, not a base-URL string — so it stays
module-local and now documents that it deliberately overrides the
conftest fixture (standard pytest name shadowing, nearest wins).
test_actions.py's `shim` fixture (make_shim_server, yields
`(state, base_url)`, conformance-mode branch) and its fake-bot
ThreadingHTTPServer fixture (~line 690) are different servers, not
copies — untouched.

**The nit:** `import http.client` removed from
tests/test_snapshot_validation.py — verified unused first (sole mention
in the module was the import line itself; the two later "make_server"
mentions are comments). Import cleanup ripple from the fixture
deletions handled the same way: `threading` dropped where the fixture
was its last user (test_api, test_auth, test_snapshot_validation,
test_views), `make_server` dropped from the five import lines, and
test_auth's now-unused `import pytest` went too; ruff clean over tests/.

Suite: **522 passed + 1 skipped** — baseline-identical, as a pure dedupe
must be; ruff `All checks passed!`; `bootstrap.py check --strict` green
at this flip (mid-slice it was red only on this card's own in-progress
badge, i.e. born-red as intended). Net −17 lines. Files:
`tests/_server_helpers.py` (new), `tests/conftest.py`,
`tests/test_actions.py`, `tests/test_api.py`, `tests/test_auth.py`,
`tests/test_server_robustness.py`, `tests/test_snapshot_validation.py`,
`tests/test_views.py`, plus records.

ORDER-038 note (adopted per control/status.md practice line,
2026-07-13T05:27:28Z): the reviewer-authenticity gate governs
cross-agent reviewer REPLIES — no reviewer reply was acted on in this
slice; if one lands on this PR, verify its cited line ranges against
EOF at the reviewed head before acting.

## 💡 Session idea

The serve() dedupe removed the five identical FACTORIES, but the raw
server LIFECYCLE boilerplate (start daemon thread over
`serve_forever` → `shutdown()` → `server_close()` → `join(timeout=5)`)
still exists in seven more places over four different server
constructors: tests/conftest.py:55 (`base_url`),
tests/test_actions.py:137 (`shim` over make_shim_server),
tests/test_actions.py:700 (fake-bot ThreadingHTTPServer),
tests/test_readiness.py:112,151,178 (three inline copies), and
tests/test_server_robustness.py:37 (the divergent serve). Guard recipe:
add `run_server(server)` to tests/_server_helpers.py — a contextmanager
that takes an ALREADY-CONSTRUCTED server and owns only the
thread-start/teardown lifecycle — then fold the seven sites onto it one
by one (constructors and yield shapes stay local; only the lifecycle
dedupes). Verified the same way as tonight: suite pinned at
522 passed + 1 skip.

## ⟲ Previous-session review

The `2026-07-13-test-infra-dedupe` card earned its keep twice over: its
💡 citations were all six accurate at HEAD (each file:line pointed at a
real `make_server(port=0, **kwargs)` copy), and its close-out nit
(http.client F401) was a ready-made one-liner this session simply
executed. Two honest dings. First, the idea's shape claim was wrong on
inspection: it called the copies "serve() contextmanagers" and ruled the
pytest fixture "the wrong shape" for per-test kwargs — they were already
fixtures yielding kwargs-taking factories, so the fixture shape was
never the problem; the salvageable core of the recipe (importable helper
module, conftest is not an import target) still drove tonight's design,
but the next reader should trust that card's citations over its shape
analysis. Second, it counted "SIX non-web suites" carrying the disease
without flagging that one of the six (test_server_robustness) diverges
in yield shape — `(host, port)` tuple, not URL — which is exactly the
copy that could NOT be collapsed; its "some wrap extra locals — keep
those wrappers" hedge gestured at this but misdescribed it. Its
close-out claims spot-checked true: the conftest stack it landed is
byte-real, web collection is 81 both sides at this session's HEAD too,
and "522 passed + 1 skipped" reproduced verbatim as tonight's baseline.
The records-pass escalation it carried forward ("next records/closeout
session must land it or drop it in one line") transfers again un-softened
— this is a code slice, not a records session.

- **📊 Model:** fable-5 · standard effort · task-class: self-initiated serve-helper dedupe — importable serve() context manager for non-web suites + unused-import nit (refactor)
