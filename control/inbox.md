# superbot-mineverse · inbox

> ORDERS to this Project. **ONE writer: the manager** — never edit this file. Report order
> progress in `control/status.md` (`orders: acked=… done=…`). Protocol: `control/README.md`.

*(no orders yet — the manager appends `## ORDER 001 · <ISO8601> · status: new` blocks here)*

## ORDER 001 · 2026-07-11T04:05:30Z · status: new
priority: P3
from: fleet-manager manager — ORDER 010 per-lane relay (provenance: fm control/inbox.md ORDER 010 + fm docs/findings/model-matrix-2026-07.md; relayed via fm PR #63; this lane was out of that session's scope — completed by the follow-up relay-completion slice)
executor: superbot-mineverse lane coordinator — next fired session
do: Model-attribution ground truth (fleet standing rule, family-level names only per Q-0262): (1) confirm the session-card template carries a `📊 Model:` line — add it if missing; (2) every fired session records the model family its own harness/environment reports (e.g. fable-5, opus-4.8, sonnet-5) on that line in its committed session card — the Routines screen is NOT a reliable attribution surface; (3) n/a — keep the standing rule.
why: the fleet model matrix (fm docs/findings/model-matrix-2026-07.md) found per-session self-report in commits is the only reliable attribution; cross-surface disagreement is evidenced (websites PR #59 squash 2c89e96: Routines screen fable-5 vs the fired card's claude-sonnet-5).
done-when: the next fired session's committed card carries a real family-level `📊 Model:` line and the template (if any) includes it.

## ORDER 002 · 2026-07-11T10:00Z · status: new
priority: P1
from: fleet-manager on coordinator direction (cse_012o8pySy5K3AV6JWoPKryZL), owner-directed
executor: superbot-mineverse seat (next wake)
do: quick self-review of this lane covering roughly the last 24h (2026-07-10 ~20:00Z → now): (1) anything that WENT WRONG — red CI runs, guard/classifier denials, walls hit, drift found, mistakes made or corrected — each with a citation (PR/run/commit); (2) anything REQUIRING OWNER ATTENTION — owner-only asks, pending vetoes, risky decisions taken decide-and-flag, spend/publish items — click-level and plain language; (3) one-line current health (what shipped, what's next). Commit the review as a dated "Self-review 2026-07-11" section in control/status.md (or this lane's report convention); mirror ⚑ owner-attention items on the heartbeat so the manager sweep collects them.
why: owner-requested fleet-wide self-review (2026-07-11), relayed by the fleet-manager coordinator on the owner's in-session instruction.
done-when: the self-review section is on main within this lane's next two wakes.

## ORDER 003 · 2026-07-12T08:30Z · status: new
priority: P1 (security ordering)
owner: SuperBot World coordinator (executor)
provenance: filed by the fleet manager — relocation of startup-prompt v3.1 W1 (prompts are STATELESS since v3.2, owner correction 2026-07-12; fleet-manager PR #108).
do: Land the login-CSRF security PR #42 (branch security/oauth-csrf-snapshot-validation) via the non-author review-merge path — ONE attempt; a denial parks it READY+green with a ⚑ owner ask at queue TOP. Standing ORDERING rule: this security fix merges BEFORE anything secrets-adjacent — the six-OAuth-env-var provisioning ask stays SUBORDINATE until #42 is in main. Then disposition security-report PR #31 (codex; merge or close with a one-line reason), and re-render .claude/CLAUDE.md via the kit so it matches the tree.
why: verified at HEAD 2026-07-12: PR #42 OPEN, mergeable_state clean at head 2557f1a; PR #31 OPEN (mergeable_state blocked); the CSRF fix is not in main (76be821).
done-when: #42 in main with the merge-commit diff showing the payload landed; #31 terminal; CLAUDE.md matches the tree.
