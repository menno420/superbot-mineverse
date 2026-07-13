# Session — 2026-07-13 — run_server lifecycle contextmanager (self-initiated)

> **Status:** `complete`
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

Shipped on `claude/run-server-lifecycle` (base: main @ dc320bf). No scope
cut. All seven cited sites re-located at HEAD first (the card's own
"line numbers may have drifted" warning was right only for
test_actions.py:700 → 702; the other six were exact).

**The helper:** `tests/_server_helpers.run_server(server)` — a plain
`@contextmanager` that takes an ALREADY-CONSTRUCTED server, starts
`serve_forever` in a daemon thread, and on exit tears down in the suites'
canonical order (`shutdown()` → `server_close()` → `join(timeout=5)`,
inside `finally`). Construction — and with it the yield shape (base URL,
`(state, url)`, `(host, port)`) — stays at each call site, exactly as the
source card's recipe prescribed.

**Collapsed (5 of the 7 cited sites), all single-server:**
tests/conftest.py `base_url` (module-scoped web fixture),
tests/test_actions.py `shim` (make_shim_server; conformance-mode early
return untouched), tests/test_readiness.py `shim` plus its two inline
probe stubs (Happy200/Bare401 — these two already had try/finally with
the identical teardown, so run_server is byte-equivalent there; the three
fixture sites had plain code-after-yield, where pytest runs teardown
regardless — run_server's `finally` is the same observable behavior).
Import ripple: `threading` dropped where a collapsed site was its last
user (conftest.py, test_readiness.py); test_actions.py keeps it
(fake_executor still uses it); ruff clean over tests/.

**Left alone (2 of the 7 cited sites + 1 uncited twin), decided and
flagged:** the factory-style fixtures that start N servers into a list
and tear them down FIRST-started-first — tests/test_actions.py
`fake_executor` (:706 loop), tests/test_server_robustness.py `serve`
(:43 loop), and `serve_factory` itself in tests/_server_helpers.py (:79
loop, the card's own PR #68 helper, same pattern though not among the
cited seven). Folding them onto run_server would need ExitStack (or
manual `__enter__`/`__exit__`), and stacked contexts unwind
LAST-started-first — a multi-server teardown-order flip, which the
zero-behavior-change rule ("shutdown/join order identical") forbids
deciding silently. No CURRENT test starts more than one server through
any of the three (call-site audit: every `fake_executor(...)` /
robustness `serve(...)` call is once-per-test), so the flip is latent,
not live — but latent order changes are exactly what "genuinely
divergent stays" is for. run_server's docstring names all three and the
reason.

Suite: **545 passed + 1 skipped** — baseline-identical, as a pure dedupe
must be; no pin added; ruff `All checks passed!`; `bootstrap.py check
--strict` green at this flip (mid-slice red only on this card's own
in-progress badge — born-red as intended). Files:
`tests/_server_helpers.py`, `tests/conftest.py`, `tests/test_actions.py`,
`tests/test_readiness.py`, plus records.

ORDER-038 note: no cross-agent reviewer reply was received or acted on in
this slice; if one lands on the PR, verify its cited line ranges against
EOF at the reviewed head before acting.

## 💡 Session idea

The lifecycle dedupe is deliberately half-finished: the three
factory-style fixtures still each carry the same list-loop teardown
(`for server, thread in servers: shutdown/close/join`) —
tests/_server_helpers.py:79 (`serve_factory`), tests/test_actions.py:706
(`fake_executor`), tests/test_server_robustness.py:43 (`serve`) — kept
apart tonight only because folding them through ExitStack would flip
multi-server teardown from first-started-first to last-started-first.
Guard recipe: settle that order question ON PURPOSE, then finish the
dedupe. Tonight's call-site audit found no test starts two servers
through any one factory, so either (a) rule LIFO acceptable (it is the
Python-idiomatic unwind order) and fold all three onto
`ExitStack` + `run_server`, or (b) keep FIFO by giving _server_helpers a
tiny `started_servers()` contextmanager owning the list+loop, and fold
the three loops onto THAT (run_server stays the single-server face).
Either way the decision gets one sentence in the helper's docstring and
the three factories converge on one teardown implementation. Re-audit
call sites first — if a multi-server test has appeared, (b) is the only
zero-behavior-change option.

## ⟲ Previous-session review

`.sessions/2026-07-13-relay-retry-after.md` reviewed at this session's
base (dc320bf, its own squash). Its close-out claims reproduced byte-real
on every spot-check: `RELAYED_RESPONSE_HEADERS` is real and
status-keyed at server/actions.py:150 (the `.get(status, ())` filter at
:164 is exactly the "Retry-After on a 200 stops at the relay" behavior
claimed); `propose` returns the 3-tuple at :205/:211 with the
case-insensitive `_relayed_headers` filter; the shim audit ("no 429, no
rate_limited, no Retry-After anywhere") reproduced as zero grep hits at
HEAD; and its "539 + 6 = 545" arithmetic matched tonight's independently
measured 545 passed + 1 skipped baseline verbatim. Its 💡 (frontend never
reads the relayed header) also verified: web/app.js still renders
rejections purely from the body (`✗ ${data.reason_code}: ${data.message}`
at :1718) with zero `res.headers` mentions — ready-made, accurately
cited, and it names its own degrade path and test venue; a strong
harvest candidate. One nit: the card's "only caller server/app.py:229"
is :232 at HEAD — drift of the exact flavor its own goal section warned
about, harmless but a reminder to keep citing functions alongside line
numbers. One structural observation, not a ding: its two decide-and-flag
records (allowlist shape, advisory missing-header) each came with the
pinning test named in the same breath — that pattern is what made
tonight's spot-check cheap, and this card copied it for the teardown-order
decision. Escalation carry, un-softened: the bare-📊-line sweep is now
EIGHT reviews old; the next records session treats "drop it in one line"
as the default.

- **📊 Model:** fable-5 · standard effort · task-class: self-initiated run_server lifecycle dedupe — single-server thread lifecycle contextmanager for the test suites (refactor)
