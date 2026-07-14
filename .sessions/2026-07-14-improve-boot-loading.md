# Session — 2026-07-14 — boot loading state in the web frontend

> **Status:** `complete`
> **Branch:** `claude/improve-boot-loading`
> **Venue:** lane worker session (owner directive 2026-07-14 improvement
> wave — "See if there is anything else you can come up with or improve,
> try to continue with as much as you can"; harvest at HEAD `58657ed`).

**Goal:** `boot()` (web/app.js:1845-1873 at base) leaves the page
header-only with every section `hidden` until `/api/views` resolves —
on a slow snapshot fetch the viewer stares at a bare header with no
signal that anything is happening. The error path already talks through
`#status-banner` (web/index.html, `showBanner`), so the fix is pure
rendering symmetry: show "Loading snapshot…" via the SAME banner
mechanism before the fetch, and hide/clear it once the snapshot is in
hand and rendering succeeds (the error path keeps overwriting the
banner exactly as today; `render()`'s own no-miners banner must NOT be
clobbered). Served-bytes pins in tests/test_web_fun.py style; the write
path stays dormant — no config/env handling anywhere near this.

## Close-out

Shipped on `claude/improve-boot-loading` (base: main @ `58657ed`). No
scope cut; pure rendering only — the write path stayed dormant, no
config/env handling touched.

Wiring, exactly the file's own grammar: a `hideBanner()` twin lands
directly under `showBanner` (same getElementById + classList shape,
inverse of every line); `boot()` calls
`showBanner("Loading snapshot…", false)` before the `/api/views`
fetch and `hideBanner()` after `res.json()` resolves — deliberately
BEFORE `render(views)`, because `render()` raises its own banner for
an empty snapshot ("Snapshot loaded, but it contains no miners.",
app.js) and a post-render teardown would clobber it. The error path is
byte-identical to before: `showBanner(\`Snapshot unavailable — …\`,
true)` overwrites the loading line, so a failed boot never strands
"Loading…" on screen. `#status-banner` already carries `role="status"`
(web/index.html), so the loading line is announced politely with zero
markup change.

Coverage (+2 tests, suite **589 passed + 1 skipped** vs the 587+1
baseline), in `tests/test_web_fun.py` served-bytes style: the loading
string ships AND precedes the `/api/views` fetch call in source order;
`hideBanner` exists, tears down immediately before `render(views)`,
and the no-miners banner string it must not clobber still ships. No
pure-logic harness pin: `hideBanner` is DOM-effectful (not a pure
top-level function), so `tests/test_js_logic.py` has nothing
observable to fold — the ordering pins carry the behavior instead.
`python3 bootstrap.py check --strict` exit 0 at flip.

## 💡 Session idea

The loading banner is honest but unbounded: `boot()`'s
`fetch("/api/views")` has no timeout (zero `AbortController`/
`AbortSignal` anywhere in web/app.js — grepped this session), so a
HUNG connection (server accepts, never responds) leaves
"Loading snapshot…" up forever, indistinguishable from a slow-but-alive
fetch; the error path only fires when the fetch settles. Guard recipe:
pass `{ signal: AbortSignal.timeout(ms) }` to the `/api/views` fetch in
`boot()` (web/app.js) — the existing catch already renders
`Snapshot unavailable — …` for the resulting AbortError/TimeoutError,
so the whole change is one option object + a named timeout constant;
pin the constant and the `signal:` option via served-bytes in
tests/test_web_fun.py. Same gap applies to `fetchMe()` and `sendAction`
if the pattern is worth generalizing — decide once, apply to all three
or deliberately to boot only.

## ⟲ Previous-session review

`.sessions/2026-07-14-readiness-ingest-leg.md` reviewed at this
session's base (58657ed). Its close-out claims reproduce byte-real:
`--probe-ingest` is a real opt-in flag (scripts/readiness_check.py:38
usage line, leg marked "NOT one of the six required" at :76),
`INGEST_RELAY_URL_ENV = "MINING_SNAPSHOT_RELAY_URL"` at :80,
`INGEST_401_REASONS = ("invalid_signature", "stale_timestamp")` at :85,
`probe_ingest_endpoint` defined at :147 with the injected
`ingest_prober=probe_ingest_endpoint` seam at :223, and
docs/live-prod-cutover.md carries the leg at :268/:284 with the
never-200 rule spelled out. tests/test_readiness.py shows 41
ingest-marked hits — consistent with the claimed loopback coverage.
Its SET/UNSET-only hygiene claim ("a value is NEVER printed") was
spot-checked at the reason-validation site (:200) and holds. No
inflation found; the card's guard-recipe discipline (env var named,
function anchors, doc section) made this review a minutes job — the
loop working as .sessions/README.md intends.

- **📊 Model:** fable-5 · standard effort · task-class: frontend boot loading state — Loading snapshot banner before /api/views resolves (build)
