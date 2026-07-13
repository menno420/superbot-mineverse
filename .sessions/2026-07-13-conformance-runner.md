# Session — 2026-07-13 — one-command conformance runner (ORDER 004 item 5)

> **Status:** `in-progress`
> **Branch:** `claude/conformance-runner`
> **Venue:** lane worker session (ORDER 004 night run — item 5, third
> piece: conformance-run prep for the moment the owner provisions
> `MINING_WRITE_ENDPOINT`/`MINING_WRITE_SHARED_SECRET`).

**Goal:** make the WRITE-contract conformance sweep a SINGLE COMMAND.
Recon established the pytest seam is complete
(`tests/test_actions.py` — `SHIM_CONFORMANCE_BASE_URL` short-circuits
the shim fixture; secret via `SHIM_CONFORMANCE_SECRET` or
`MINING_WRITE_SHARED_SECRET`, missing → pytest exit 4; reachability
smoke test included; audit assertions skip by design — the manual
checklist item) and `docs/live-prod-cutover.md` §1 documents the prose
command — none of that is rebuilt. What's missing and gets built here:
(1) `scripts/conformance_run.py` — stdlib-only wrapper in
`scripts/readiness_check.py`'s style: env presence check (names only,
never values), opt-out unsigned endpoint probe (the readiness-check
handshake), then the pytest sweep with output captured to a
timestamped, git-ignored results file and a clear PASS/FAIL verdict
pointing at the manual 3-step audit verification as the explicit next
step; distinct exit codes for pass / sweep-fail / probe-fail /
missing-env. (2) `docs/conformance-runbook.md` — one page: purpose,
prerequisites, the single command, PASS/FAIL semantics (incl. the
pytest exit-4 missing-secret path and the fixture-reload fine print),
audit follow-on, rollback pointer. (3) `tests/test_conformance_run.py`
— the runner's pure parts (env resolution, verdict formatting), no
network, in `tests/test_readiness.py`'s style.

## 💡 Session idea

(placeholder — filled at close-out)

- **📊 Model:** fable-5 · standard effort · task-class: conformance-run prep — one-command runner + runbook (tooling)
