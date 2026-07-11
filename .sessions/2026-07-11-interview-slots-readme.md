# Session 2026-07-11 — interview slots + README

> **Status:** `complete`

## Plan

Fill the remaining substrate-kit interview slots that are objectively
derivable, render, and expand the root README (mission, safety architecture,
staged ladder, layout, agent orientation). Ship as one PR on
`claude/interview-slots-readme` with auto-merge (squash) armed.

## Close-out

- Interview finished: answered `integration_mode` = `guided` (Q-001) and
  confirmed the two provisional derived slots `project_name` =
  `superbot-mineverse` (Q-002) and `doc_roots` = `docs` (Q-007). All 13 slots
  now `filled`; `bootstrap.py ask` reports no pending questions.
- `bootstrap.py render --live`: 0 unfilled placeholders across planted docs
  (the ORDER 000 session had already rendered the content slots; no doc
  churn from this session).
- README.md rewritten: mission + safety architecture (no Postgres, no bot
  token, versioned read contract, bot-side audited action endpoint for
  future writes), staged ladder 0/a/b/c/d with stage 0 done (PR #2) and
  stage a next, local run + test commands, repo layout, agent orientation
  pointer.
- Deliberately untouched: `control/status.md`, `control/inbox.md`
  (single-writer files), `.sessions/2026-07-11-session.md` (the ORDER 000
  session's card — a stop-hook auto-draft had appended to it in the working
  tree; reverted to HEAD so this PR only ADDS a card and the gate's
  advisory-sentinel lane applies).
- verify: `python3 -m pytest -q` → 11 passed.
- Decisions made: answer only objectively derivable slots; leave nothing
  provisional; keep `docs/current-state.md` untouched (suggested follow-up:
  record this PR there once merged).
- Next session should know: interview is done (`ask` is empty); stage-a work
  (read contract v1, `docs/mining-data-contract.md` + `schemas/`) is being
  added by a sibling session — rebase on main before extending the README's
  layout table with `schemas/`.

## 💡 Session idea

The `ask` quota hides already-known answers: a session that knows a slot
value from committed docs (e.g. `mode` already `guided` in state) should be
able to run `bootstrap.py ask --all` and settle every remaining slot in one
pass instead of rediscovering the bank across sessions.

## ⟲ Previous-session review

The ORDER 000 session's card was left born-red by design but a stop-hook
auto-draft later appended `[[fill:]]` slots to it in the working tree, which
made every later local `check --strict` red on someone else's card; workflow
improvement — a session that inherits a dirty sibling card should revert it
and note the revert, never complete another session's judgment slots.

- **📊 Model:** fable-5 · standard effort · task-class: docs+config (interview/render/README)
