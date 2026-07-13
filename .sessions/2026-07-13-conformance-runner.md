# Session — 2026-07-13 — one-command conformance runner (ORDER 004 item 5)

> **Status:** `complete`
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
command — none of that is rebuilt. Built here: the operational wrapper
(`scripts/conformance_run.py`), the one-page runbook
(`docs/conformance-runbook.md`), and pure-part tests
(`tests/test_conformance_run.py`).

## Close-out

Shipped on `claude/conformance-runner` (base: PR #60's head fab4819 —
main did not yet carry the write-path-hardening stack; noted in the PR
body).

**The single command:** `python3 scripts/conformance_run.py` on a
shell carrying the owner-provisioned values. Decide-and-flag calls
made inside it:

- **Base-URL derivation:** when `SHIM_CONFORMANCE_BASE_URL` is unset,
  the base is DERIVED from `MINING_WRITE_ENDPOINT` by stripping the
  contract route `/relay/mining/action` — the provisioned web host can
  run the sweep with zero extra exports. An endpoint that doesn't end
  with the contract route refuses to guess and names the explicit
  export instead.
- **Secret display:** one deliberate, bounded deviation from
  `readiness_check.py`'s never-anything rule — the secret prints as a
  sha256 8-hex fingerprint + length (never the value, and URLs are
  never printed at all), because a shared-secret MISMATCH between the
  web host and the bot host is the most likely conformance failure and
  a fingerprint lets two hosts compare without exposure.
- **Results location:** timestamped logs under `.conformance-runs/`
  IN the repo but git-ignored (added to `.gitignore`) — discoverable
  next to the code and safe from /tmp cleanup, structurally
  uncommittable. Never commit results files.
- **Exit codes:** 0 pass · 1 sweep failed · 2 probe failed · 3 env
  missing/underivable; the seam's own pytest exit 4 maps to 3, and 4
  is deliberately unused by the wrapper so it can never masquerade as
  the seam's abort (pinned by test).
- **Probe default-on** (`--skip-probe` to omit): the unsigned
  readiness handshake is reused via importlib from
  `readiness_check.probe_endpoint` — one probe implementation, not
  two — and fails fast (exit 2) before a long sweep.

Verified end to end with the shim as the "external" executor
(`python3 tests/shim/shim_bot.py`, then the runner with only
`MINING_WRITE_ENDPOINT` + `MINING_WRITE_SHARED_SECRET` exported):
derivation, fingerprint, probe ok, 44 passed + 1 skipped, VERDICT:
PASS, exit 0, log landed git-ignored. Misconfigured (exit 3) and
probe-fail (exit 2) paths exercised live too.

Coverage (+18 tests, suite **520 passed + 1 skip** from 502 + 1):
`tests/test_conformance_run.py` — env resolution (explicit/derived/
underivable/absent), secret precedence + empty-string-as-unset,
fingerprint non-reversibility, sentinel-leak assertions on every
report/verdict line, verdict mapping incl. the exit-4 seam path,
distinct-exit-codes pin, timestamped results naming, gitignore pin,
and the no-subprocess `main()` missing-env path.

Docs: `docs/conformance-runbook.md` (badge `reference`, one page:
purpose / prerequisites / the command / PASS-FAIL semantics incl. the
fixture-reload fine print / the manual 3-step audit follow-on /
rollback pointer to cutover §4), linked from
`docs/live-prod-cutover.md` §1's first checkbox for docs-gate
reachability.

## 💡 Session idea

The three env-diagnostic surfaces now overlap without sharing code:
`readiness_check.py` (six names, SET/UNSET), `conformance_run.py`
(base-URL derivation + secret fingerprint), and the seam's own guard
inside `tests/test_actions.py`. A tiny `scripts/_envlib.py` (or a
shared section in one script) holding the canonical name constants and
the resolution rules would keep a future rename (e.g. a v2 contract
route) from needing three synchronized edits — the derivation rule
`MINING_WRITE_ENDPOINT minus ACTION_PATH` is now load-bearing in two
places (runner + runbook prose). Guard recipe: a cross-module test
pinning that `conformance_run.ACTION_PATH == shim_bot.ACTION_PATH` and
that the env names match `readiness_check.REQUIRED_ENV_VARS`'s tail —
cheap, and it would have to be deleted (loudly) to drift.

## ⟲ Previous-session review

The `2026-07-13-write-path-hardening` card is a strong close-out: the
chosen-semantics paragraph (never relay a non-conformant envelope on
ANY status; distinct 502 so "executor gone" ≠ "executor lying") reads
as a decision record, not a diff summary, and the `_UnhandledKeyword`
re-raise subtlety is exactly the kind of fail-loud fine print that
saves the next session a debugging hour. Its argument-only timeout
seam (NOT an env var — host surface stays the documented pair) held up
as doctrine tonight: this session likewise added ZERO new host env
names, deriving the sweep's base URL from the pair the host already
carries. Its 💡 lru_cache-on-schema-loads idea is still unlanded and
still right-sized. One transcription nit: the card says the envelope
validator is "~30 lines" while `server/response_validation.py` is
meaningfully larger with the applicator extensions — harmless, but
close-out size claims should match the shipped file. The carried
records-pass nit (bare-`📊 Model:` sweep on the 2026-07-12 cards:
land it or drop it) is now six reviews old — flagging it for the next
records/closeout session to DECIDE, not re-carry.

- **📊 Model:** fable-5 · standard effort · task-class: conformance-run prep — one-command runner + runbook (tooling)
