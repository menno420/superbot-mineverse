# Session — 2026-07-13 — relay contract-relevant executor headers (Retry-After on 429)

> **Status:** `complete`
> **Branch:** `claude/relay-retry-after`
> **Venue:** lane worker session (coordinator green-light wave — generative
> rung: decide-and-flag, CI-green, flip-race practice).

**Goal:** land the recorded 💡 from
`.sessions/2026-07-13-status-coherence-check.md` (PR #69): the contract
promises a `Retry-After` header (integer seconds) on every 429
`rate_limited` rejection (docs/mining-write-contract.md § Rate limits and
the HTTP status mapping table's 429 row), but `server/actions.py::propose`
returned only `(status, body)` — `res.headers` / `err.headers` were
dropped — and `_serve_action` set only its own
Content-Type/Length/Cache-Control, so a relayed 429 reached the browser
WITHOUT the backoff hint the contract promises clients.

Baseline measured on base main @ 5a12fee (PR #69's squash):
**539 passed + 1 skipped**.

## Close-out

Shipped on `claude/relay-retry-after` (base: main @ 5a12fee). No scope cut.

**Allowlist decision (decided and flagged):** the relay forwards an
ALLOWLIST of contract-relevant executor response headers, never a blanket
passthrough (executor headers can carry executor-internal details). The
contract names exactly one client-facing header — `Retry-After` on the 429
`rate_limited` row — so the allowlist is
`actions.RELAYED_RESPONSE_HEADERS = {429: ("Retry-After",)}`, keyed by
status so a `Retry-After` an executor attached to a 200 stops at the relay
too. Pinned by test; growing it is a contract decision (extend the mapping
AND the prose together).

**Presence decision (the source card's flagged candidate):** a 429 MISSING
`Retry-After` stays ADVISORY — it relays without the header, never a 502.
The header is the executor's contract obligation; the coherence layer
judges status↔body pairings, and refusing a coherent, conformant 429 over
a missing client hint would turn a hint gap into an outage. The relay also
never invents a value. Pinned by test both ways.

**Shim decision: no shim change.** `tests/shim/shim_bot.py` has NO
rate-limit path at all — no 429, no `rate_limited`, no `Retry-After`
anywhere (grep + call-site audit) — so there was no header-less 429 path
to fix; per the task rule the shim stays untouched and the new pins run
against the canned `fake_executor` (which grew an `extra_headers` seam).
Flagged: the reference impl silently lacks the whole § Rate limits
behavior (see 💡-adjacent note below).

**Wiring:** `propose` returns `(status, body, relayed_headers)` where
`relayed_headers` is the already-filtered allowlist subset
(`_relayed_headers`, case-insensitive via urllib's `email.message.Message`
on both `HTTPResponse` and `HTTPError`); `_serve_action` forwards them on
the RELAY path only — both 502 refusal paths (unreachable/timeout and
invalid-executor-response) never leak an executor header. Only caller
(`server/app.py:229`) updated; no test called `propose` directly.

Coverage (+6 tests, suite **545 passed + 1 skipped**), all in
`tests/test_actions.py`: allowlist equality pin; 429 + `Retry-After: 7`
relays the header verbatim; 429 without the header still relays (and no
header is invented); an unallowlisted header stops at the relay even on
429; a non-429 never gains executor headers (`Retry-After` included);
a refused 429 (garbage body → 502) leaks nothing. Conformance + coherence
behavior unchanged — all pre-existing envelope/coherence tests pass
untouched. Contract prose gained one sentence in § Web session → suid
binding naming the allowlist relay (it was silent on the web-relay side;
the executor-side promise at § Rate limits stands as written); Status
badge untouched in the first 12 lines.

ORDER-038 note: no cross-agent reviewer reply was received or acted on in
this slice; if one lands on the PR, verify its cited line ranges against
EOF at the reviewed head before acting.

## 💡 Session idea

The header now reaches the browser but the frontend never reads it:
`web/app.js::sendAction` handles a rejection purely from the body
(`✗ ${data.reason_code}: ${data.message}`) and never touches
`res.headers`. Guard recipe: on `res.status === 429`, read
`res.headers.get("Retry-After")` (same-origin fetch — readable without
CORS ceremony), and when it parses as a positive integer show
"rate limited — retry in Ns" and disable the action buttons for that
window (a countdown re-enable beats a silent dead button). Degrade
gracefully when the header is absent (the relay guarantees it's never
invented): keep today's message. Pin in the JS-logic harness
(tests/test_js_logic.py) if the parse/format helper is extracted pure.
Related smaller gap, flagged in the close-out: the shim has no rate-limit
path at all, so the contract's § Rate limits row (burst 10/10 s → 429 +
`Retry-After`) has no executable reference form — a tiny shim burst
limiter would let conformance mode probe the one row nothing exercises.

## ⟲ Previous-session review

`.sessions/2026-07-13-status-coherence-check.md` reviewed at this
session's base (5a12fee, its own squash). Its 💡 — this session's source —
reproduced byte-real on every claim: `propose` returned only
`(status, body)` with `res.headers`/`err.headers` dropped (actions.py
171–177 pre-change), `_serve_action` set only its own three headers
(app.py 253–257 pre-change), and the contract's 429 row + § Rate limits
promise the header (lines 130, 168). Its close-out claims spot-checked
clean too: "539 passed + 1 skip" was tonight's measured baseline verbatim
on 5a12fee; `EXPECTED_HTTP_STATUS` is real at
server/response_validation.py:63; the shim audit's "11 emitted pairings,
no 429" matches tonight's independent call-site grep (16 `_response`/
`_reject_audited` sites collapsing to the 11 claimed distinct pairings,
zero rate-limit paths). Even its flagged decide-and-flag candidate
(429-missing-header: incoherent or advisory?) was the exact decision this
slice had to make — a card whose open question became the next session's
work is the loop behaving. Escalation carry, un-softened: the
bare-📊-line sweep escalation is now SEVEN reviews old; per the previous
card's own ruling, the next records session treats "drop it in one line"
as the default.

- **📊 Model:** fable-5 · standard effort · task-class: recorded 💡 follow-up — Retry-After relay allowlist on the write path (build)
