# Session 2026-07-11 — pytest into the enforced merge path (investigation + owner ask)

> **Status:** `complete` *(single-PR session: the card is added and closed in
> the same commit; an ADDED card gates advisory in CI per
> `.github/workflows/substrate-gate.yml`.)*

## Plan

Follow-up to PR #7 (schema gate): the new `schema-gate.yml` workflow runs
`python3 -m pytest -q` on every PR, but its check (context `pytest`) is NOT
required on `main` — only `substrate-gate` is — so auto-merge does not wait
for it (PR #7 merged 7s before its own pytest check finished). Determine
whether the kit offers a repo-side way to put pytest into the ENFORCED merge
path: (a) additional required contexts via `substrate.config.json`, or (b) a
sanctioned project-test hook inside the kit gate. Implement if so; otherwise
produce the exact owner ask. Also: add the missing `schemas/` row to the
README repo-layout table.

Constraints honored: read-only stack untouched; `control/status.md` /
`control/inbox.md` / `substrate-gate.yml` untouched (single-writer /
kit-owned). No work claim filed: this is a single-PR session — a claim lands
on main only inside the same squash-merge as the finished work, so it would
be born-stale and protect nothing (claims exist to cover the pre-build gap).

## Close-out

- **Path (a) — NO.** `substrate.config.json` → `automerge.required_context`
  is a single string and explicitly **informational only**: it labels the
  enabler's log lines; "a wrong name here mislabels a log line, never the
  guard" (`bootstrap.py` `_default_automerge`, and again in
  `automerge_enabler_workflow`: "the guard itself counts contexts
  generically"). No list form, no second key.
- **Path (b) — NO.** The kit gate runs only `bootstrap.py check` variants;
  engine code bans `subprocess`, so `check` cannot run project tests, and
  the `verify_command` slot is card-drafting prose ("the engine cannot
  execute commands"). Hand-adding a pytest job inside the kit-owned gate is
  the exact anti-pattern the kit's `gate_carveouts` detector exists for
  (the superbot-games #16 class — a regen would silently delete it). The
  sanctioned shape is a SEPARATE host-owned workflow — which PR #7 already
  shipped (`.github/workflows/schema-gate.yml`, job `pytest`).
- **Enforcement is GitHub-native and owner-only.** The enabler arms native
  auto-merge (`gh pr merge --auto`); GitHub merges when the BASE branch's
  ruleset-required contexts are green. The kit's own adopt checklist says
  so: "these are the owner-UI toggles a planted workflow CANNOT set for
  itself... a workflow has no path to repo settings"
  (`bootstrap.py` `_repo_settings_checklist`).
- **The owner ask (routed via PR body; next status overwrite should carry
  it as ⚑ needs-owner):** in the `main` ruleset (Settings → Rules →
  Rulesets → the rule requiring `substrate-gate`), add a second required
  status check with context exactly **`pytest`** (the job id in
  `schema-gate.yml`; verified via the checks API on PR #7's head — check
  run name `pytest`). One click-path change; no repo file changes needed.
- Shipped repo-side: `schemas/` row in the README repo-layout table; this
  card.
- verify: `python3 -m pytest -q` → 25 passed. `python3 bootstrap.py check
  --strict` → "all checks passed" (exit 0) with this card in the tree.
- Guard recipe (deferred): once the owner adds `pytest` to the ruleset, the
  NEXT `claude/*` PR should demonstrate enforcement — compare its merge
  timestamp against the `pytest` check-run `completed_at` (checks API);
  merge must not precede it. Config is not read from the PR branch for
  this, so no PR can demonstrate its own enforcement change.

## 💡 Session idea

The `substrate-gate` job and the `pytest` job both `pip`-less-checkout the
same tree; a tiny badge row in the README (substrate-gate + schema-gate
status badges) would make "which gates exist and are they green" visible
without opening the Actions tab.

## ⟲ Previous-session review

The read-contract-v1 card's close-out already flagged that pytest "was NOT
previously enforced by any workflow" — that one line made this follow-up
slice trivially routable. Friction: the card said it, but nothing routed it
to the owner; an unenforced gate discovered mid-session should become a
⚑ needs-owner item in the SAME session's status overwrite, not just a card
footnote.

- **📊 Model:** fable-5 · standard effort · task-class: CI-enforcement investigation + owner ask (ops)
