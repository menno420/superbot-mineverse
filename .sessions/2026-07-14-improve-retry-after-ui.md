# Session — 2026-07-14 — frontend reads Retry-After on 429

> **Status:** `in-progress`
> **Branch:** `claude/improve-retry-after-ui`
> **Venue:** lane worker session (owner directive 2026-07-14 improvement
> wave — "See if there is anything else you can come up with or improve,
> try to continue with as much as you can"; harvest at HEAD `58657ed`,
> lane F PR 2 of 2, built after #97's squash).

**Goal:** land the recorded 💡 from
`.sessions/2026-07-13-relay-retry-after.md`: the relay now delivers the
contract's `Retry-After` header on 429 `rate_limited` rejections
(allowlist pinned by tests/test_actions.py) but
`web/app.js::sendAction` renders rejections from the BODY alone
(`✗ ${data.reason_code}: ${data.message}`) and never touches
`res.headers` — the backoff hint dies in the browser's network tab.
Per the card's guard recipe: on `res.status === 429` read
`res.headers.get("Retry-After")` (same-origin fetch — readable without
CORS ceremony); when it parses as a positive integer, append
"— retry in Ns" to the existing rejection line; extract a pure
`retryAfterText()` helper so tests/test_js_logic.py can pin it. Degrade
gracefully when the header is absent (the relay never invents one):
today's message, byte-identical. Pure rendering only — the write path
stays dormant, no config/env handling.

## Close-out

_(pending)_
