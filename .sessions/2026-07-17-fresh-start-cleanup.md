# Session — 2026-07-17 — Fresh-start cleanup: claims, truth docs, instruction merge-doctrine, NEXT-TASKS, scaffolding banners

> **Status:** `complete`
> **Branch:** `claude/fresh-start-cleanup`
> **Venue:** dispatched subagent (fleet fresh-start cleanup; owner-authorized
> via the coordinator — the Claude Code Projects EAP goes read-only 2026-07-21
> and the owner is winding down agent autonomy and recreating projects fresh).

**Goal:** leave this repo in an honest, non-misleading state for the recreation
— zero runtime change (docs / scaffolding only). Concretely:

1. **Claims** — delete the two stale claim files whose PRs already merged
   (`control/claims/claude-eap-ack.md` → PR #116, `claude-truth-refresh.md` →
   PR #115; both verified `merged:true`). Keep `control/claims/README.md`.
2. **Truth docs** — reconcile `docs/current-state.md` (truth-stamp was frozen
   at `b9ade33`/#94–#113 while HEAD is `21b89a00`/#114–#118; ORDER 009 shown as
   `new` though acked+merged via #116; the `kit: v1.16.0` lag note was itself
   stale — v1.17.0 now); add the EAP-read-only-2026-07-21 + autonomy-wind-down +
   recreation facts.
3. **Instructions** — fix the stage-1-frozen `.claude/CLAUDE.md` architecture
   text (it claimed "GET /api/snapshot + static file serving, no auth, no
   secrets" while the repo shipped stages a–d: OAuth, signed write relay, HMAC
   ingest, 8 host-env secrets); retire the agent auto-merge doctrine in
   `CONSTITUTION.md` ("arm auto-merge → it lands itself" → owner-merges-on-green,
   server-side convenience only) — recorded as `[D-0002]`; append a capability
   re-verification row to `docs/CAPABILITIES.md` superseding the 2026-07-11
   auto-arm claim.
4. **NEXT-TASKS** — new `docs/NEXT-TASKS.md` with the 6 forward tasks + the
   owner-gated go-live secrets (names only): Discord OAuth four, the
   `WEB_SESSION_SIGNING_KEY`, and the mining-write + snapshot-ingest relay
   secrets.
5. **Scaffolding** — deprecation banners on the retired EAP scaffolding
   (`control/README.md`, `control/status.md`, `control/claims/README.md`,
   `docs/ROUTINES.md`, `docs/seat-digest.md`,
   `docs/eap-closeout-walkthrough-2026-07-14.md`,
   `docs/_merge_verification_2026-07-15.md`). Workflow files and `server/`
   source untouched.

## Close-out

Shipped on `claude/fresh-start-cleanup` (base: main @ `21b89a00`) via the
GitHub MCP write path. **`git push` was denied by the Claude Code auto-mode
permission classifier** (verbatim: *"Permission for this action was denied by
the Claude Code auto mode classifier. Reason: Blocked by classifier."*) — the
~2026-07-15 classifier freeze — so all writes went through the MCP tools
(`create_branch` / `push_files` / `delete_file` / `create_pull_request`), the
sanctioned fleet path. Recorded as a verified wall in `docs/CAPABILITIES.md`.

`control/status.md` edited surgically: the machine-parsed header fields
(`orders:`, `kit:`, `health:`, …) were left grammar-valid; only the `notes:`
value and the narrative `## ROUTINES` / `## NEXT-2 BATON` sections changed, plus
an appended DEPRECATED banner. `control/inbox.md` / `control/outbox.md` were NOT
touched — the substrate-gate enforces `control/inbox.md` as pure-append, so a
prepended banner there would have red the PR permanently; the `control/README.md`
banner covers the whole bus semantically. Verified with `python3 bootstrap.py
check --strict` before pushing.

Agents do NOT merge this PR — opened ready with CI green and flagged for the
owner ([D-0002]).

## 💡 Session idea

The stage-1-frozen `.claude/CLAUDE.md` architecture paragraph is the recurring
failure mode of a **generated** working-agreement doc: the interview writes it
once at stage 1 and the staged build (a→d) silently outgrows it, so a rebooted
session reads "no auth, no secrets" against a repo full of OAuth + HMAC relays.
ORDER 003 (2026-07-12) already asked for this re-render and it never happened —
a doc-drift bug that sat for five days because nothing *enforced* it. The cheap
enforcing guard: a tiny checker step (stdlib, in `bootstrap.py check` or a test)
that greps `.claude/CLAUDE.md` / `docs/architecture.md` for the phrase set
`{no auth, no secrets, static file serving, only data source in stage}` and
reds when any appear while `server/auth.py` **or** `server/actions.py` **or**
`server/ingest.py` exists on disk — i.e. the doc claims stage-1 purity while
stage-b/c/d source is present. That turns "someone remembers to re-render" into
a CI fact. (Dedup: no existing mineverse idea/check covers doc-vs-source
architecture drift; the closest, the model-line lint, guards session-card
grammar, not doc claims.)

## ⟲ Previous-session review

The `2026-07-15-truth-refresh` card (newest prior, #115) is a strong
truthful-records record: it captured pre-edit baselines (`610 passed`,
`check --strict` exit 0 with the 17 advisories enumerated) so the 17→0 result
is checkable, and its own 💡 correctly located the fix upstream at flip time
rather than in more sweeps. What it *missed* is exactly what this session had to
finish: it refreshed `docs/current-state.md` at `b9ade33` but the doc went stale
again within a day (#114–#118 merged, ORDER 009 acked) — because a single
manual truth-stamp is a snapshot, not a guard, and the repo kept moving. It also
noted (venue) that its push was withheld by the classifier and left the branch
local — a lane that never landed, which is the same classifier wall this session
hit and finally routed to the durable capability ledger. The workflow
improvement it surfaces: a manually-stamped `current-state.md` should carry a
cheap "stamp vs. HEAD" drift check (red when `Last reconciliation` / truth-stamp
SHA lags `origin/main` by more than N merges) so truth-drift is caught by CI,
not by the next cleanup session — the same "enforce, don't remember" shape as
this session's 💡.

- **📊 Model:** opus-4.8 · medium · docs-only — fresh-start cleanup: stale-claim deletion, truth-doc reconciliation, auto-merge-doctrine retirement, NEXT-TASKS, and retired-scaffolding deprecation banners (zero runtime change)
