# Session — 2026-07-14 — staleness-literal drift guard (test-only)

> **Status:** `complete`
> **Branch:** `claude/improve-stale-drift-guard`
> **Venue:** improvement-wave lane E (owner directive 2026-07-14; wave
> claim `control/claims/claude-improvement-wave-2026-07-14.md`, #95).

**Goal:** the 180 s / 60 s staleness numbers live in three places —
`server/views.py:52-53` (`SNAPSHOT_CADENCE_SECONDS` /
`STALE_AFTER_SECONDS`, the VERDICT-056-measured constants) and
`web/app.js` `?? N` fallbacks at :740-741 (header staleness line) and
:910 (`snapshotIsStale` card idle check) — but the only test coverage
is `tests/test_web_fun.py:118` pinning the literal STRING
`"staleness?.stale_after_seconds ?? 180"`, which asserts nothing about
the server constants: change views.py and the frontend fallbacks drift
silently. Add one test that regex-extracts every numeric
`stale_after_seconds ?? N` / `cadence_seconds ?? N` fallback from the
served `web/app.js` bytes and asserts each equals the corresponding
`server/views.py` constant, in the style of the existing js-pin tests
(tests/test_js_logic.py `shipped_konami_sequence` regex extraction;
tests/test_web_fun.py served-bytes `js` fixture). Test-only — no
runtime change; suite 587 → 588.

## Close-out

Shipped on `claude/improve-stale-drift-guard` (base: main @ `8ea5aff`,
the #96 README-refresh squash). One new test,
`tests/test_web_fun.py::test_staleness_fallbacks_match_views_constants`,
placed directly after `test_idle_state_pins` in the idle-miners
section:

- `re.findall(r"stale_after_seconds \?\? (\d+)", js)` +
  `r"cadence_seconds \?\? (\d+)"` over the SERVED `js` fixture bytes —
  position-independent, so the guard follows the literal wherever it
  moves inside app.js (today: :740-741 header line, :910
  `snapshotIsStale`).
- Count floors (`>= 2` stale, `>= 1` cadence) so a DROPPED fallback is
  drift too, then set-equality against `views.STALE_AFTER_SECONDS` /
  `views.SNAPSHOT_CADENCE_SECONDS` — the schema-independent
  prose-sourced constants VERDICT 056 priced (views.py:41-53).
- In-function `sys.path` + `from server import views`, mirroring
  tests/test_js_logic.py:483-486 (the shipped-catalog seam test) —
  test_web_fun.py stays a served-bytes module at the top level.

Test-only: no runtime file touched. Hunted for sibling twins before
closing: no other `?? N` in app.js shadows a server constant (the rest
are honest `?? 0` / `?? "?"` placeholders), so this pair was the whole
drift surface.

Verified pre-flip in this container: `python3 -m pytest -q` →
**588 passed, 1 skipped** (587 baseline + 1 new);
`python3 bootstrap.py check --strict` exit 0 (tails in the PR body).

## 💡 Session idea

`test_idle_state_pins` (tests/test_web_fun.py:114-119) still pins the
raw string `"staleness?.stale_after_seconds ?? 180"` — now that the
numeric guard exists, that hard-coded 180 means a LEGITIMATE retune of
`views.STALE_AFTER_SECONDS` needs two test edits instead of one and
the string pin goes red for the wrong reason. Follow-up: interpolate —
`f"staleness?.stale_after_seconds ?? {views.STALE_AFTER_SECONDS}"` —
keeping the structural pin while sourcing the number from the one
constant. Left out of this diff deliberately: the wave item was scoped
to an ADDITIVE guard, and rewriting an existing pin is a separate
judgment call. Guard recipe: tests/test_web_fun.py
`test_idle_state_pins`, one-line change, needs the same in-function
views import this session added two tests below. Dedupe checked: no
session card, `docs/ideas/` entry, or test comment proposes it — the
string pin predates any views import in this file.

## ⟲ Previous-session review

The `2026-07-14-improve-readme-refresh` card (this lane's previous
session, merged #96) survives spot-checking: its file:line citations
replay clean at `8ea5aff` (server/app.py:109-113 route constants,
ingest env names server/ingest.py:54,57, badge-scan exemption
bootstrap.py:1593-1613 — all still hold), and the "names only, never a
value" rule was actually kept in the shipped README diff. Two honest
dings: (1) its close-out asserts "every claim cross-checked against
HEAD" but records no negative space — it never says what it checked
and chose NOT to change (the `tests/` layout row, the missing
`scripts/` row), so a reader can't distinguish "verified fine" from
"not looked at"; this card names its negative result (no sibling
literal twins) explicitly for that reason. (2) Its 💡 (README
endpoint-list drift guard) is well-anchored and this session is
adjacent evidence the pattern works — but it sits ungated with no
consumer named beyond "a test", the same watcher-less-idea failure
mode the readiness-ingest-leg card already called out two cards ago;
the lane keeps diagnosing that disease without curing it.

- **📊 Model:** fable-5 · standard effort · task-class: staleness-literal drift guard — JS fallback numbers pinned to server/views.py constants (test-only)
