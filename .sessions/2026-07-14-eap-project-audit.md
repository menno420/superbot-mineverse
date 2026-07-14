# Session — 2026-07-14 — EAP project close-out audit (three-repo seat audit)

> **Status:** `complete`
> **Branch:** `claude/eap-project-audit`
> **Venue:** worker session (coordinator dispatch — seat-wide EAP close-out
> audit; superbot-mineverse is the landing repo, superbot-games and
> superbot-idle read as evidence sources only).

**Goal:** land `docs/audits/eap-project-audit-2026-07-14.md` — the seat's
definitive EAP close-out audit covering all three repos (superbot-games,
superbot-idle, superbot-mineverse). Every claim cites path@SHA / PR# /
CI run / verbatim quote; "not measured" beats invention.

## Close-out

Shipped on `claude/eap-project-audit` (base: main @ `cb57d02`, the #90
audit squash). Four commits, flip-last choreography:

1. Born-red claim (`df7efcf`): in-progress card + claim file
   `control/claims/2026-07-14-eap-project-audit.md` + telemetry row
   (Q-0194 — row rides the same PR as the card).
2. The audit doc + `docs/AGENT_ORIENTATION.md` planted-doc index line
   (reachability) (`1e4d92d`).
3. Heartbeat overwrite of `control/status.md` (`6415509`): fresh stamp,
   plain `kit: v1.15.0` line, orders carried done=001–007, the three
   standing ⚑ needs-owner items preserved verbatim, audit-doc pointer;
   `control/inbox.md` untouched.
4. This flip commit: card → complete, claim released.

The doc covers (11 sections, mandated order): measured seat scale (222
cards / 525 main commits / 370 PRs, 369 merged, 1 closed-unmerged, 0
open); tooling verdicts; the walls ledger with verbatim denials and
FLEET-FIX/ANTHROPIC/ACCEPTED dispositions; landing friction (medians
4.05 / 0.4 / 1.48 min; the owner-click → enabler collapse under fm ORDER
029; enabler 0 observed failures; 126 stale branches); scheduling
friction (fresh-session cron 0-for-2, no trigger tombstones, INC-17);
platform issues; ceremony paid vs taxed (all recent substrate-gate reds
were designed born-red holds: games 20/40, idle 13/25, mineverse 7/120;
the kit added-card fail-open as a Q-0120 checker's-bug instance); twelve
self-fixes; five ranked pains with paste-ready asks; a deduped wishlist;
and honest gaps (incl. the STEP 0 delta — games #102 / idle #112 /
mineverse #90 had ALL merged before this audit ran — and the fact that
no literal "EAP close-out" inbox order exists anywhere: the audit is
dispatch-borne).

Verified pre-flip in this container at commit 3: `pip install
jsonschema==4.26.0` (requirements-dev.txt) then `python3 -m pytest -q` →
**610 passed, 1 skipped in 111.29s**; `python3 bootstrap.py check
--strict` → exit 1 with exactly the two designed-hold lines for this
card ("HOLD (by design)"), zero docs-gate findings on the new doc.
Re-run at this flip: strict check green (tail recorded in the PR).

## 💡 Session idea

This audit's two hardest measurement losses were platform-transient, not
evidence-transient: the GitHub MCP token expired mid-mining (killing
per-PR `merged_by` attribution for 101 mineverse + most idle PRs) and
MCP pagination caps sampled only ~120 of 652/699 CI runs — yet the bulk
pulls that DID complete lived only in a session-scratch directory that
dies with the container. Commit the evidence, not just the conclusions:
give `docs/audits/` a `data/` convention — each audit lands its machine
tables (per-PR created/merged/minutes TSV, per-run workflow conclusions)
beside the prose, so the NEXT audit deltas committed baselines instead
of re-pulling 370 PRs through a token that may expire. Anchor: the
per-PR tables behind §4 of `docs/audits/eap-project-audit-2026-07-14.md`
already exist as clean TSVs; the convention costs one subdirectory and a
line in the audit template. Guard recipe: data files are dated and
append-never (a new audit adds new files), so no drift target exists.
Dedupe checked: no session card, `docs/ideas/` entry, or the games/idle
💡 pools carry this (the nearest neighbor — games truth-stamp's
"hand-transcribed SHAs" 💡 — is about prose citations, not committed
evidence tables).

## ⟲ Previous-session review

The `2026-07-14-snapshot-contract-constant` card is a strong close-out
to inherit from: its "deliberately NOT imported by server/*" paragraph
is the rare record of a change *not* made with the load-bearing reason
(the flat-launch import dance) written down where the next refactorer
will trip over it, and its parity-audit section separates
probe-confirmed facts from the two first-hand edges it found itself
(level minimum mismatch, nullable slots) — exactly the confirmed/new
split this audit needed fleet-wide. Two nits: its 💡's "gated on the
seam ruling" framing never names WHERE the ruling will arrive (an inbox
ORDER? a sim-lab verdict relay? — the waiter can't watch a mailbox it
can't name), and the card cites `menno420/idea-engine@2e5d73f` capture
paths without noting that repo is outside this session's MCP scope — a
future session verifying provenance will hit the §3 scope wall this
audit documents. Its worktree-isolation line ("never the shared clone's
checked-out tree") is this session's practice too.

- **📊 Model:** fable-5 · standard effort · task-class: EAP close-out project audit — three-repo measured audit doc + landing (audit)
