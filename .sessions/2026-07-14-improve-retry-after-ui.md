# Session — 2026-07-14 — frontend reads Retry-After on 429

> **Status:** `complete`
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

Shipped on `claude/improve-retry-after-ui` (base: main @ `d207b9d`,
after #97's squash plus the #99–#104 sibling-lane merges). No scope
cut; pure rendering only — the write path stayed dormant.

Wiring, the recipe followed to the letter: a pure `retryAfterText()`
lands directly under `showActionResult` (web/app.js) — strict
integer-seconds parse (`/^\d+$/` on the trimmed string, so HTTP-date
Retry-After forms, negatives, floats, `1e3`/`0x07` exponent/hex
lookalikes and junk all return `""`; `0` parses but yields no hint) —
and `sendAction`'s rejected branch appends
`retryAfterText(res.headers.get("Retry-After"))` gated on
`res.status === 429`, so no other rejection can ever grow a
header-derived suffix and an absent header leaves today's message
byte-identical (the relay never invents a value; neither does the UI).
Same-origin fetch, so the header is readable with no CORS ceremony —
exactly as the source card promised. The recipe's second half (disable
the action buttons for the window + countdown re-enable) was NOT
landed — it needs timer state threaded through `renderActionPanel` and
is a deliberate scope cut recorded in the source card already, not
re-recorded here.

Coverage (+3 tests, suite **605 passed + 1 skipped** = base `d207b9d`'s
602+1 plus these): 2 pure-vector pins in `tests/test_js_logic.py`
(positive-integer formatting incl. leading/trailing-space tolerance;
10 absent/junk forms — `null`, `""`, `"0"`, `"-3"`, `"7.5"`, `"junk"`,
an HTTP-date, `"7s"`, `"1e3"`, `"0x07"` — all `""`), 1 served-bytes pin
in `tests/test_web_fun.py` (helper ships; hint gated on
`res.status === 429`; the header is actually READ; suffix rides the
existing rejection line). `python3 bootstrap.py check --strict` exit 0
at flip.

## 💡 Session idea

An accepted action changes the world but not the page: `sendAction`'s
accepted branch shows `✓ ${data.message}` and stops — the views
rendered at boot stay frozen, so a successful `mine`/`buy` leaves
coins/depth/inventory visibly stale until a manual reload (grep this
session: zero `setInterval`/`location.reload`/re-fetch anywhere in
web/app.js; `boot()` fetches `/api/views` exactly once). Guard recipe:
extract boot()'s fetch-validate-render block into a `refreshViews()`
used by both `boot()` and the accepted branch of `sendAction`
(web/app.js) — the loading/error banner semantics from #97 come along
for free; debounce is unnecessary at one refresh per accepted action.
Pin via served-bytes ordering (accepted branch calls `refreshViews()`)
in tests/test_web_fun.py. Distinct from the source card's still-open
countdown/disable follow-up and from the shim burst-limiter gap it also
records — neither is duplicated here.

## ⟲ Previous-session review

`.sessions/2026-07-13-relay-retry-after.md` — this session's source —
reviewed at base `d207b9d`. Its 💡 reproduced byte-real on every
frontend claim: `sendAction` rendered rejections from the body alone
(`✗ ${data.reason_code}: ${data.message}`, pre-change web/app.js:1752)
with zero `res.headers` reads anywhere in the function, and the
relay-side promises it leans on are all live at this HEAD —
`RELAYED_RESPONSE_HEADERS == {429: ("Retry-After",)}` pinned at
tests/test_actions.py (allowlist-equality test), verbatim-relay and
never-invented pins beside it, exactly as the card's close-out lists.
Its guard-recipe discipline held up in practice: function + file + test
target named meant this slice started coding in minutes — the card even
pre-answered the CORS question (same-origin fetch) that would otherwise
have cost a detour. One honest wrinkle: the recipe's suggested copy
("rate limited — retry in Ns") was adapted to the file's existing
rejection-line grammar (`✗ reason_code: message — retry in Ns`) since
the reason_code already says rate_limited — following the source's
intent over its literal string. Its flagged shim burst-limiter gap
remains open and recorded there; not duplicated here.

- **📊 Model:** fable-5 · standard effort · task-class: recorded 💡 follow-up — frontend reads Retry-After on 429, retry-in hint on the rejection line (build)
