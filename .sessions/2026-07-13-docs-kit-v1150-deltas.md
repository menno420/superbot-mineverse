# Session — 2026-07-13 — kit v1.15.0 lane-owed docs deltas

> **Status:** `complete` — scope: the two docs deltas PR #80 left lane-owed
> **Branch:** `claude/docs-kit-v1150-deltas`
> **Venue:** coordinator-dispatched worker session (docs-only slice —
> the two template deltas PR #80 left lane-owed).

**Goal:** apply the kit v1.15.0 upgrade's outstanding docs deltas that
PR #80 (merged; main was `1520e05` after it) recorded as lane-owed in
`.substrate/upgrade-report.md` § "Template deltas for diverged docs":
bring `docs/CAPABILITIES.md`'s Append-log preamble to the venue-token
six-field format (the capability-seed fence itself was already refreshed
at upgrade), and apply the remaining `docs/AGENT_ORIENTATION.md`
template hunks (preflight boot section, SKILLS/ROUTINES routing
paragraphs, verify pointer) beyond the read-path list hunk #80
hand-merged. Template structure ONLY — every host-specific recorded
finding (the CAPABILITIES.md append-log ledger entries, the mineverse
contract/auth/cutover reading routes) survives verbatim.
`control/status.md`'s diverged delta is NOT in scope (one-writer file;
PR #81 already landed its kit-line fix on main `e81c9ff`).

## Close-out

Shipped as PR #82 on `claude/docs-kit-v1150-deltas` (base: main @
`e81c9ff`, which includes #81). Docs only, no code. Delta source of
truth: the upgrade report's rendered template diffs, cross-checked
against the reference shapes at superbot-games `d6a9526` and
superbot-idle `96cd635` (games carries the new CAPABILITIES append-log
preamble byte-identically; both siblings applied the AGENT_ORIENTATION
delta only partially, so mineverse's own report diff was authoritative
there). Coherence check that motivated the preflight hunk: the v1.15.0
`.claude/CLAUDE.md` applied in #80 already says "Mechanics + safety
notes: `docs/AGENT_ORIENTATION.md` § 'Start every session'" — until
this PR that pointed at the OLD boot list, not the preflight mechanics.
Verified pre-flip in this container: `python3 -m pytest -q` →
`551 passed, 1 skipped`; `bootstrap.py check --strict` → exit 1 with
ONLY the designed born-red HOLD for this card (plus the pre-existing
never-exit-affecting `owner-action-fields` advisory on
`control/status.md`, untouched here). All six 2026-07-11 host
append-log entries in `docs/CAPABILITIES.md` confirmed preserved
(zero removed ledger lines in the diff). The slice's claim file is
removed in this flip commit, so `control/claims/` = README only at
merge.

## 💡 Session idea

The upgrade report renders each diverged doc's full template@old →
template@new diff, but once a session hand-merges PART of it (as #80
did with the read-path list hunk), nothing tracks what remains: this
session had to mentally three-way-diff the report, the live file, and
two sibling repos to establish that the CAPABILITIES fence was done,
the append-log preamble was not, and one of three AGENT_ORIENTATION
hunks had landed — and the siblings show the failure mode at scale
(games `d6a9526` applied the routing paragraph but not preflight; idle
`96cd635` applied neither; nobody can see this without doing the same
archaeology). Have the kit grow a `bootstrap.py upgrade
--remaining-docs` report that re-diffs each diverged doc's CURRENT
bytes against template@new (slot-rendered, same machinery the upgrade
report already uses) and prints only the still-unapplied hunks — making
lane-owed template debt mechanically enumerable per repo instead of
re-derived per session. Dedup-checked: #80's idea is pre/post sha256
pairs for the carve-out scan (auditing kit-owned CI files, not doc
debt); the games wave's idea is seat-digest report classes; no card or
ideas doc here proposes remaining-delta enumeration.

## ⟲ Previous-session review

The previous card (`2026-07-13-kit-upgrade-v1150.md`, PR #80) drew its
lane-owed boundary precisely and it held: everything it deferred was
still genuinely outstanding at this session's boot (the CAPABILITIES
append-log preamble and the three non-list AGENT_ORIENTATION hunks
replayed cleanly from its report against the live files), and
everything it claimed done WAS done — the seed fence it reported as
"already current" is byte-level identical to the games reference. Its
💡 idea also has the fastest idea-to-action turnaround in this repo's
card history: within the hour, #81's outbox relayed the
upgrade-report-sha256-pairs ask to the kit lab (it is in #81's merge
title on main `e81c9ff`). One nit: the card says the docs delta
"stays lane-owed" without naming a tracking home, which is exactly why
this session needed a coordinator prompt (and the report archaeology
above) to find the debt — see this card's 💡.

- **📊 Model:** fable-5 · standard effort · task-class: kit-upgrade docs follow-up — v1.15.0 lane-owed template deltas for CAPABILITIES + AGENT_ORIENTATION (docs-only)
