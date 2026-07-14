# Session — 2026-07-14 — boot loading state in the web frontend

> **Status:** `in-progress`
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

_(pending)_
