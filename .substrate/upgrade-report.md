# substrate-kit upgrade report — v1.8.0 → v1.15.0

> Generated 2026-07-13 by `bootstrap.py upgrade`. Rollback: `python3 bootstrap.py upgrade --rollback`.

**Docs:** consumer-edited: 3 · diverged: 3 · template-improved: 5 · unchanged: 13

| planted doc | class | note |
|---|---|---|
| CONSTITUTION.md | template-improved | consumer-untouched + template improved — safe to apply with `upgrade --apply-docs` |
| docs/decisions.md | unchanged | template identical across versions |
| docs/architecture.md | unchanged | template identical across versions |
| docs/ownership.md | unchanged | template identical across versions |
| docs/runtime_contracts.md | unchanged | template identical across versions |
| docs/repo-navigation-map.md | unchanged | template identical across versions |
| docs/helper-policy.md | unchanged | template identical across versions |
| docs/collaboration-model.md | template-improved | consumer-untouched + template improved — safe to apply with `upgrade --apply-docs` |
| docs/ai-project-workflow.md | unchanged | template identical across versions |
| docs/owner-profile.md | unchanged | template identical across versions |
| docs/AGENT_ORIENTATION.md | diverged | both the template and the doc moved — manual merge |
| docs/current-state.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| docs/question-router.md | template-improved | consumer-untouched + template improved — safe to apply with `upgrade --apply-docs` |
| docs/CAPABILITIES.md | diverged | both the template and the doc moved — manual merge |
| docs/SKILLS.md | unchanged | template identical across versions |
| docs/ROUTINES.md | unchanged | template identical across versions |
| docs/ideas/README.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| .session-journal.md | unchanged | template identical across versions |
| control/README.md | template-improved | consumer-untouched + template improved — safe to apply with `upgrade --apply-docs` |
| control/inbox.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| control/status.md | diverged | both the template and the doc moved — manual merge |
| control/claims/README.md | unchanged | template identical across versions |
| scripts/env-setup.sh | unchanged | template identical across versions |
| .claude/CLAUDE.md | template-improved | consumer-untouched + template improved — safe to apply with `upgrade --apply-docs` |

## Carve-out scan

- carve-out scan: .github/workflows/substrate-gate.yml — ran, 0 found
- carve-out scan: .github/workflows/auto-merge-enabler.yml — ran, 0 found

## Capability-ledger seed refresh

- capability-seed: docs/CAPABILITIES.md fence already current — nothing to refresh.

This upgrade ships the venue-scoped capability ledger (grounded-skills §4.2): entries carry a venue token (owner-live · autonomous-project · routine-fired · subagent · any) and the ledger's kit-owned seed block carries the posture decision rule. If this repo carries a local prose copy of the boot-triad/venue-posture rule (superbot Q-0270), that copy is now superseded by docs/CAPABILITIES.md's posture rule — collapse the local copy into a pointer.

## Seat-digest refresh

- seat-digest: docs/seat-digest.md already current — nothing to refresh.

## Applied (--apply-docs)

- applied: CONSTITUTION.md (template@new, hash re-recorded)
- applied: docs/collaboration-model.md (template@new, hash re-recorded)
- applied: docs/question-router.md (template@new, hash re-recorded)
- applied: control/README.md (template@new, hash re-recorded)
- applied: .claude/CLAUDE.md (template@new, hash re-recorded)

## Template deltas for diverged docs

### docs/AGENT_ORIENTATION.md

```diff
--- docs/AGENT_ORIENTATION.md (template@old, current slots)
+++ docs/AGENT_ORIENTATION.md (template@new, current slots)
@@ -7,11 +7,24 @@
 
 ## Start every session
 
-1. `.claude/CLAUDE.md` — the working agreement.
-2. `docs/current-state.md` — the living status ledger.
-3. `docs/CAPABILITIES.md` — verified session capabilities & walls (the
-   discovery rule lives there; append what you learn).
-4. This file — task-specific reading routes.
+**Preflight first — land on origin's HEAD before reading anything else:**
+
+```
+git fetch origin main && git reset --hard origin/main
+```
+
+(or `git checkout -B main origin/main`; substitute your default branch).
+Then verify: local HEAD (`git rev-parse HEAD`) must equal
+`git ls-remote origin main`. A warm container clone can lag origin by
+dozens of commits, and a stale clone reads stale orders and stale state —
+every orientation read below assumes this step already ran. The hard reset
+discards uncommitted local changes by design: at session START there should
+be none; if `git status` shows work you did not author, stop and report it
+instead of resetting over it.
+
+The boot set lives in the working agreement — `.claude/CLAUDE.md` — and its
+orientation guidance (one list, one home). This file is not boot reading —
+open it when a task needs a route into the deeper docs.
 
 ## Binding contracts
 
@@ -28,11 +41,20 @@
 `docs/collaboration-model.md` · `docs/helper-policy.md` ·
 `docs/repo-navigation-map.md` · `docs/ai-project-workflow.md` ·
 `docs/owner-profile.md` · `docs/current-state.md` · `docs/decisions.md` ·
-`docs/question-router.md` · `docs/CAPABILITIES.md` · `docs/ideas/README.md` — plus the root
+`docs/question-router.md` · `docs/CAPABILITIES.md` · `docs/SKILLS.md` ·
+`docs/ROUTINES.md` · `docs/ideas/README.md` — plus the root
 `CONSTITUTION.md` (the working agreement) and `.session-journal.md`.
+
+Recurring action? **`docs/SKILLS.md`** — the skill index — names every
+kit-shipped skill and when to reach for it; check it before improvising a
+procedure.
+
+Arming, deleting, or auditing a scheduled trigger/routine/wake chain?
+**`docs/ROUTINES.md`** — binding choice, delivery verification,
+probe-not-record, scheduler-health signatures, pacing — read it before
+touching the trigger registry.
 
 ## Verifying any change
 
-```
-python3 -m pytest -q
-```
+See the working agreement (`.claude/CLAUDE.md`) and its verify guidance
+(one home, never two copies).
```

### docs/CAPABILITIES.md

```diff
--- docs/CAPABILITIES.md (template@old, current slots)
+++ docs/CAPABILITIES.md (template@new, current slots)
@@ -16,53 +16,97 @@
 hand reminders. This ledger makes capability knowledge durable across
 sessions: one session's discovery is every later session's starting fact.
 
+<!-- substrate-kit:capability-seed BEGIN — kit-owned, refreshed at upgrade. Append your findings BELOW the fence (## Append log), never inside it. -->
+
+## Posture decision rule — establish your venue first
+
+- **Owner-live session:** assume NO special limitations apply — act and merge
+  directly (superbot Q-0269).
+- **Autonomous / routine-fired seat:** pre-route around every known stall
+  class recorded below; park only on a REAL denial, never preemptively
+  (superbot Q-0270 boot triad: model · venue · ability envelope).
+
+Venue tokens (every entry names where it was verified): `owner-live` ·
+`autonomous-project` · `routine-fired` · `subagent` · `any`. Capabilities are
+**venue-scoped, not global** — the same operation can work owner-live, be
+org-refused on a cross-session binding, and prompt-stall in a plain-started
+seat while never prompting in a Routine-spawned one (fleet night review,
+2026-07-12). A flat CAN/CANNOT ledger is wrong somewhere by construction.
+
 ## THE DISCOVERY RULE
 
 Before declaring anything impossible, and before assuming a tool or
 credential is missing:
 
-1. **Check this file** — the capability or wall may already be recorded.
+1. **Check this file** — the capability or wall may already be recorded for
+   your venue.
 2. **Check the environment** — `printenv` / list the available tools BEFORE
    assuming no credentials exist (provisioned env tokens are routinely
    forgotten, not absent).
 3. **Attempt once** — try the operation and capture the **exact** error text;
    a guessed wall and a verified wall are different facts.
 4. **Append the finding same session** — capability or wall, dated, with the
-   evidence (exact error, or proof it worked) and the workaround if one was
-   found. An unrecorded discovery is re-paid by every future session.
+   venue token, the evidence (exact error, or proof it worked) and the
+   workaround if one was found. An unrecorded discovery is re-paid by every
+   future session.
+5. **Staleness — re-verify what you build on**: an entry older than the
+   staleness window (config `cadence.staleness_days`, default 14) that your
+   work depends on is a **claim, not a fact** — re-verify it with one cheap
+   attempt and append the result. Re-verifications APPEND, never edit: a
+   refuted wall can self-resolve platform-side, and a ledger with no
+   freshness data is confidently stale — worse than ignorant.
 
 ## Capabilities — verified working
 
-- **Media is readable**: a video is never "unviewable" — extract frames
-  (`ffmpeg -i in.mp4 -vf fps=1 frame_%04d.png`) and read the images; same
-  idea for audio (transcribe) and PDFs (render pages). Try the recipe before
-  reporting a format wall.
-- **Provisioned credentials**: the environment often carries tokens/keys as
-  env vars — `printenv` first; a missing-looking credential is usually a
-  missing *look*.
-- **Release cutting despite the tag wall**: `workflow_dispatch` on the
-  release workflow (with a version input) creates the tag in-Actions —
+- `any` · **Media is readable**: a video is never "unviewable" — extract
+  frames (`ffmpeg -i in.mp4 -vf fps=1 frame_%04d.png`) and read the images;
+  same idea for audio (transcribe) and PDFs (render pages). Try the recipe
+  before reporting a format wall. — LAST-VERIFIED: 2026-07-10
+- `any` · **Provisioned credentials**: the environment often carries
+  tokens/keys as env vars — `printenv` first; a missing-looking credential is
+  usually a missing *look*. — LAST-VERIFIED: 2026-07-10
+- `any` · **Release cutting despite the tag wall**: `workflow_dispatch` on
+  the release workflow (with a version input) creates the tag in-Actions —
   proven repeatedly fleet-wide after direct tag pushes 403'd.
+  — LAST-VERIFIED: 2026-07-12
 
 ## Walls — verified blocked (use the workaround; don't rediscover)
 
-- **Tag push / release create via git**: HTTP 403 from the environment's git
-  proxy → use the workflow_dispatch release path.
-- **Branch deletion**: 403 on every path (git push `:branch` and API) →
-  owner deletes by hand / enables "Automatically delete head branches".
-- **`api.github.com` direct HTTP**: blocked → GitHub access is MCP-tools-only.
-- **Environment / routine / Project creation**: owner-click actions in the
-  console — queue them under `⚑ needs-owner`, never wait silently.
-- **Self-merge classifier**: sessions can be refused merging owner-gated PRs
-  while their other capabilities work — and the boundary differs by session
-  kind (a child session was refused where a coordinator was not). Record
-  which kind of session hit which boundary.
-- **GraphQL API quota**: tight — batch queries and prefer the REST-backed
-  MCP tools for bulk reads.
+- `any` · **Tag push / release create via git**: HTTP 403 from the
+  environment's git proxy → use the workflow_dispatch release path.
+  — LAST-VERIFIED: 2026-07-12
+- `any` · **Branch deletion**: 403 on every path (git push `:branch` and
+  API) → owner deletes by hand / enables "Automatically delete head
+  branches". — LAST-VERIFIED: 2026-07-10
+- `any` · **`api.github.com` direct HTTP**: blocked → GitHub access is
+  MCP-tools-only. — LAST-VERIFIED: 2026-07-10
+- `any` · **Environment / Project creation**: owner-click actions in the
+  console — queue them as structured owner asks, never wait silently.
+  Routine/schedule creation is NO LONGER a blanket wall: `create_trigger`
+  arms routines agent-side (proven 2026-07-11); the console-only knobs
+  (model class, branch-push, auto-fix PRs) remain owner-only.
+  — LAST-VERIFIED: 2026-07-11
+- `subagent` · **Self-merge classifier**: sessions can be refused merging
+  owner-gated PRs while their other capabilities work — and the boundary
+  differs by venue (a child session was refused where a coordinator was
+  not). Record which venue hit which boundary. — LAST-VERIFIED: 2026-07-10
+- `any` · **GraphQL API quota**: tight — batch queries and prefer the
+  REST-backed MCP tools for bulk reads. — LAST-VERIFIED: 2026-07-10
+- `routine-fired` · **Silent prompt-stalls**: a permission prompt in an
+  unattended seat is a silent stall, and grant boundaries differ by venue —
+  the same tool call can be pre-granted in a Routine-spawned seat and prompt
+  in a plain-started one. Pre-route around recorded stall classes; verify
+  grants per venue, never globally. — LAST-VERIFIED: 2026-07-12
+
+<!-- substrate-kit:capability-seed END -->
 
 ## Append log — newest first
 
-Format: `- YYYY-MM-DD · capability|wall · finding · evidence · workaround`.
+Format: `- YYYY-MM-DD · capability|wall · <venue> · finding · evidence · workaround`
+(venue ∈ `owner-live` · `autonomous-project` · `routine-fired` · `subagent` ·
+`any`; older five-field lines without a venue token stay valid — read them
+as venue `any`.)
 
-(Hand-filled by sessions, per the discovery rule. Seed walls/capabilities
-above came from the fleet's lived 2026-07 findings; local ones go here.)
+(Hand-filled by sessions, per the discovery rule. Seed rows above are
+kit-owned — they refresh at upgrade between the fence markers; local
+findings go here, below the fence.)
```

### control/status.md

```diff
--- control/status.md (template@old, current slots)
+++ control/status.md (template@new, current slots)
@@ -13,3 +13,8 @@
 The `kit:` line is your kit self-report (substrate-coordinator visibility): keep the version in
 sync with your vendored kit on every upgrade, `check:` = your last `check --strict` verdict,
 `engaged:` = the post-adopt engagement gate (yes once `check` reports ENGAGED/green live CI).
+Keep the `kit:` token PLAIN — the bold-label form `- **kit:** v1.2.3 · check: green · engaged: yes`
+does NOT parse and the fleet registry reads it as no `kit:` line at all (grammar + the valid
+bold-label-before-plain-token shape: `control/README.md` § "status.md format"). And this line is
+a self-report, not version truth — self-reports chronically lag; the kit repo's generated
+`docs/adopters.md` and your committed tree are the version truth to defer to.
```

