# Claim

- `claude/server-robustness` · **server HTTP robustness — charset on every Content-Type, sha256 ETag + If-None-Match 304 on /api/snapshot + /api/views, honest 404/405 with Allow headers, malformed-snapshot 5xx guard (+ regression tests)** — server/app.py + tests/test_server_robustness.py · server/ tests/ · 2026-07-11

Removal of this claim file is deferred to the next control-lane PR, per the
established pattern (a build PR never mixes in control/ deletions).
