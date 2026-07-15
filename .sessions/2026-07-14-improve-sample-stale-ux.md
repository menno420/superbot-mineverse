# Session — 2026-07-14 — sample-vs-live stale-badge UX

> **Status:** `complete`
> **Branch:** `claude/improve-sample-stale-ux`
> **Venue:** improvement-wave lane G (owner directive 2026-07-14; wave
> claim `control/claims/claude-improvement-wave-2026-07-14.md`, #95).

**Goal:** the committed sample's `generated_at` is days old, so the
demo PERMANENTLY renders the red "⚠ STALE — snapshot 3d old, expected
every 60s" alarm plus 💤 idle marks on every miner
(web/app.js `renderStaleness` :724-755, `snapshotIsStale` →
`renderMinerCard` :1084-1089) — a false alarm by construction, since
the server KNOWS the bytes came from the committed sample
(server/app.py `snapshot_path_from_env` :98-107 — `MINING_SNAPSHOT_PATH`
unset → `SNAPSHOT_PATH`). Fix: additive `staleness.source:
"sample"|"live"` key in the `/api/views` staleness block
(server/views.py `build_staleness` :571-585); frontend renders a
neutral "committed sample data — live relay not connected" notice
instead of the STALE alarm and skips the 💤 idle marks when
`source === "sample"`; live behavior byte-identical. CAUTION honoured:
tests/test_web_fun.py:118 pins `"staleness?.stale_after_seconds ??
180"` — kept intact (the source short-circuit is ADDED above the
existing math, no pinned substring moves).

## Close-out

Shipped on `claude/improve-sample-stale-ux` (base: main @ `fe2306a`,
the #98 drift-guard squash):

- server/views.py: `build_staleness(snapshot, source="sample")` gains
  the additive `"source"` key (passed through verbatim);
  `build_views(snapshot, source="sample")` threads it. Every other
  staleness key byte-identical — pinned by the new additivity test.
- server/app.py: new `MineverseHandler._snapshot_source()` — `"sample"`
  iff `self.snapshot_path == SNAPSHOT_PATH` (path identity, no content
  sniffing; an embedder-passed COPY of the sample file honestly reads
  "live"); `_serve_views` passes it to `build_views`.
- web/app.js `renderStaleness`: `source === "sample"` → neutral
  `"committed sample data — live relay not connected"` line (new
  `.staleness.sample` class, muted italic in web/style.css) instead of
  the permanent false "⚠ STALE" alarm; `snapshotIsStale` short-circuits
  false on the same check so the 💤/"(idle)" marks stay off demo cards.
  Live behavior untouched: both source checks sit ABOVE the existing
  age math, and every pinned substring (test_web_fun.py:118's
  `staleness?.stale_after_seconds ?? 180`, the idle-mark pins, the
  drift-guard regex counts) still matches — verified before commit.
- Tests (+4, suite 588 → 592): test_views.py source default +
  live-threading + additivity; test_snapshot_validation.py served-route
  case (env unset → `"sample"`, `MINING_SNAPSHOT_PATH` set to the valid
  fixture → `"live"`); test_web_fun.py pins the notice string and
  counts BOTH js source checks (`== 2`).

Verified pre-flip in this container: `python3 -m pytest -q` →
**592 passed, 1 skipped**; `python3 bootstrap.py check --strict` exit 0
(tails in the PR body).

## 💡 Session idea

The neutral sample notice drops the timestamp entirely — a demo viewer
can no longer see WHICH sample vintage they're looking at (the old
STALE line at least said "3d old"). `renderStaleness` already holds
`staleness.generated_at` in scope in that branch; appending it —
`committed sample data (generated 2026-07-11) — live relay not
connected` — keeps the notice neutral while restoring data-vintage
honesty. Guard recipe: web/app.js `renderStaleness` sample branch (the
early-return added this session) + the string pin in
tests/test_web_fun.py
`test_sample_source_gets_neutral_notice_not_the_stale_alarm` — one
branch, one pin update. Dedupe checked: no session card and no
docs/ideas entry (founding-day backlog greps clean for stale/sample)
proposes surfacing the sample's generated_at in the header.

## ⟲ Previous-session review

`2026-07-14-improve-stale-drift-guard` (lane E, merged #98 — the card
whose guards this session had to not-break) survives replay at
`fe2306a`: the regex guard fired correctly as a REVIEW aid here (this
diff adds no `?? N` fallbacks, and the guard's count-floor semantics
meant the added source short-circuit couldn't red it), and its negative
claim — "no other `?? N` in app.js shadows a server constant" —
re-verified true this session (the remaining `??` are honest `?? 0` /
`?? "?"` placeholders; re-grepped, not trusted). Two dings: (1) its 💡
(interpolate the raw `?? 180` string pin in `test_idle_state_pins`)
remains unactioned and this session ADDED another raw-string pin test
directly below that one — each wave session narrows scope honestly,
but the lane now has two adjacent pin tests and zero takers for the
one-line interpolation; the idea needs a consumer, not a third
restatement. (2) Its close-out says "tails in the PR body" for both
verify commands but the card itself records only the pytest count, not
the bootstrap tail — fine while squash-merge preserves PR bodies,
brittle if provenance ever has to be replayed from the repo alone;
this card repeats the same economy, so the ding cuts both ways.

- **📊 Model:** fable-5 · medium · feature build — sample-vs-live stale-badge UX — additive staleness.source key + neutral demo notice, live path unchanged
