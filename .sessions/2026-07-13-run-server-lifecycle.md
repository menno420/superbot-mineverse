# Session — 2026-07-13 — run_server lifecycle contextmanager (self-initiated)

> **Status:** `in-progress`
> **Branch:** `claude/run-server-lifecycle`
> **Venue:** lane worker session (coordinator green-light wave — generative
> rung: decide-and-flag, CI-green, flip-race practice).

**Goal:** harvest the recorded 💡 from
`.sessions/2026-07-13-serve-helper-dedupe.md` (PR #68's card): the serve()
dedupe removed the five identical factories, but the raw server thread
LIFECYCLE boilerplate (start daemon thread over `serve_forever` →
`shutdown()` → `server_close()` → `join(timeout=5)`) still exists at ~7
sites over four different server constructors — the card cites
tests/conftest.py:55 (`base_url`), tests/test_actions.py:137 (`shim`) and
:700 (fake-bot ThreadingHTTPServer), tests/test_readiness.py:112/151/178,
and tests/test_server_robustness.py:37 (the divergent serve). Recipe: add
`run_server(server)` to `tests/_server_helpers.py` — a contextmanager
taking an ALREADY-CONSTRUCTED server that owns only the
thread-start/teardown lifecycle — and fold the genuinely-identical sites
onto it (constructors and yield shapes stay local; only the lifecycle
dedupes). Genuinely-divergent sites stay, with a stated reason.

Zero behavior change: thread daemon-ness, shutdown/join order, and
timeouts identical; suite count pinned at the measured baseline.

Baseline measured on base main @ dc320bf (PR #70's squash):
**545 passed + 1 skipped**.

## Close-out

_(pending)_

- **📊 Model:** fable-5 · standard effort · task-class: self-initiated run_server lifecycle dedupe — single-server thread lifecycle contextmanager for the test suites (refactor)
