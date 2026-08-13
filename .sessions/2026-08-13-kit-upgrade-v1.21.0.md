# 2026-08-13 — substrate-kit v1.20.1 → v1.21.0 (distribution wave, phase 3)

> **Status:** `complete` — branch `claude/substrate-kit-v1-21-0`, PR #144. This
> flip releases the born-red hold; the reviewed head is `08c303c` and after it
> came the real gate revert the round-2 dispositions concede and prove
> (`178a0e1`, hash-verified) and this flip.

- **📊 Model:** fable-5 · high · mechanical refactor

## previous-session review

The previous card (project closeout) left the staged web app parked; nothing
it recorded contradicted this session's tree (vendored v1.20.1, pin v1.20.1,
no `kit:` self-report line — matching the registry cell).

## Shipped

- Vendored dist v1.20.1 → v1.21.0 (sha256 `8807a00e…9cc7356` four ways), pin →
  1.21.0. Rollback banked byte-identical:
  `.substrate/backup/bootstrap-1.20.1.py`.
- Gate regen REVERTED to main's version — for real in `178a0e1` after the
  round-1 attempt was a measured no-op (`git checkout HEAD --` against the
  committed regen; conceded in the thread): the new template's pytest step
  installs only `requirements.txt`, this repo keeps deps in
  `requirements-dev.txt`, and the REQUIRED gate would have stayed red past the
  flip (upstream row 16). Enabler untouched (already current).
- `docs/SKILLS.md` + `docs/collaboration-model.md` applied via
  `upgrade --apply-docs` (template-improved, consumer-untouched); digest and
  index agree.

## Follow-up owed (named, not hidden)

The kit-owned capability-seed fence in `docs/CAPABILITIES.md` differs from kit
form, so the v1.21.0 seed's retractions (branch-deletion / tag-push /
direct-HTTP walls) did NOT refresh in — sessions here still read those stale
walls until the fence is restored to kit form per the upgrade report's
documented manual step. Deferred at the review cap as its own change class.

## Verify

- `python3 bootstrap.py check --strict` → exit 1 on exactly the designed hold.
- Codex: two rounds, 9 findings — 3 adopter-side conceded+fixed (one of them
  the false revert claim itself), 1 deferred with reason (the fence), 5
  dist-routed upstream. Cap reached, opens named.

💡 A "revert" of a file already committed regenerated is invisible to
`git diff` against HEAD — the byte-identity check must run against the
MERGE-BASE version, which is what the round-2 fix does and what the
upgrade-distribution skill should say explicitly.
