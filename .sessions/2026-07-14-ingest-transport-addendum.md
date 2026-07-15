# Session — 2026-07-14 — ingest-transport spec addendum to the READ contract

> **Status:** `complete`
> **Branch:** `claude/ingest-transport-addendum`
> **Venue:** lane worker session (ORDER 006 item 3 — EAP final-night
> worklist; ORDER 007 doctrine in force: correctness outranks speed,
> no gate relaxed).

**Goal:** record the FLAG-1 transport/auth seam in
`docs/mining-data-contract.md` so both repos share ONE written seam
(ORDER 006 item 3: "record #2058's env-var names, cadence, ingest-auth
decision"). The code shipped in #88 (`POST /api/snapshot/ingest`,
`server/app.py` + `server/ingest.py`, HMAC per the canonical
`server/actions.py` scheme) and the sender half lives in superbot
PR #2058 — but the contract doc still describes only the envelope and
delivery cadence, with the transport facts scattered across the #88
docstrings and the flag1-snapshot-ingest session card's evidence trail.
Ship: a transport & authentication section in the contract doc — sender
env names (`MINING_SNAPSHOT_RELAY_URL` / `MINING_SNAPSHOT_RELAY_GUILD_ID`)
and push behavior, receiver endpoint + HMAC scheme
(`X-Mineverse-Signature`/`X-Mineverse-Timestamp`, string-to-sign,
constant-time, signature before ±300 s skew), the
`MINING_SNAPSHOT_RELAY_SHARED_SECRET` / `MINING_SNAPSHOT_PATH` env pair
with the fail-closed 503 rule, the full response status contract, and
the last-write-wins/no-sequence-key ordering semantics — every fact
verified against the code at HEAD before it is written down. Docs-only;
zero behavior; 575 passed + 1 skipped stays the bar.

## Close-out

Shipped on `claude/ingest-transport-addendum` (base: main @ `72536b1`,
after the #89 verdict-citation squash). One doc, zero behavior:

- `docs/mining-data-contract.md` gains **§ Ingest transport &
  authentication (FLAG-1 seam)** between Delivery expectations and
  Enforcement: sender half (superbot #2058 — `MINING_SNAPSHOT_RELAY_URL`
  full-URL semantics, `MINING_SNAPSHOT_RELAY_GUILD_ID`, ~60 s cadence +
  on-demand `push_now()`, 10 s timeout, failures absorbed with NO retry,
  no transport auth named in #2058), receiver half (`POST
  /api/snapshot/ingest`, the canonical `server/actions.py` HMAC scheme —
  `X-Mineverse-Signature`/`X-Mineverse-Timestamp`, string-to-sign
  `POST\n/api/snapshot/ingest\nTIMESTAMP\nsha256_hex(BODY)`,
  constant-time, signature before the ±300 s window), the
  `MINING_SNAPSHOT_RELAY_SHARED_SECRET`/`MINING_SNAPSHOT_PATH` host-env
  pair with fail-closed 503, atomic tmp+fsync+`os.replace` persist into
  the file the read routes re-read fresh, the full 200/401/400/413/415/
  405/503/500 status table, and the ordering semantics (last-write-wins
  whole-document, replay-in-window idempotent by content, NO sequence
  key in v1, staleness stays `generated_at`-based).
- Purpose paragraph amended so the old "no auth" line stops
  contradicting the seam recorded five sections later.

Fact discipline: every receiver claim was re-verified against the code
at HEAD before writing (`server/app.py:340-425` handler order +
`:173-215` 405/Allow, `server/ingest.py:54-111` env names/bounds/persist,
`server/actions.py:26-51,92-141` scheme + verify order); the three
sender facts this repo cannot verify (`MINING_SNAPSHOT_RELAY_GUILD_ID`,
`push_now()`, the draft state) are attributed to #2058 in the text
rather than asserted as local truth.

Verified pre-flip in this container: `python3 -m pytest -q` →
**575 passed, 1 skipped** and `python3 bootstrap.py check --strict`
green except the designed born-red hold on this card (flipped by this
commit).

## 💡 Session idea

`.claude/CLAUDE.md` § Architecture still asserts "the server never
writes; no database, no auth, no secrets anywhere in this repo" — false
since #82 (FLAG-2 `/api/action` relay) and doubly so since #88 + this
addendum: the boot-set doc every session reads FIRST now contradicts
the contract doc it routes to. It is kit-rendered ("NOT SOURCE OF
TRUTH", re-render after the interview fills slots), so hand-editing it
is the wrong fix. Guard recipe: update the staged-interview architecture
slot to name the two authenticated POST seams (write relay + snapshot
ingest, both host-env-secret, both fail-closed) and `bootstrap render`;
verify with `bootstrap.py check --strict` + a grep that "never writes"
is gone from the rendered file. Dedup checked: no session card, docs/
ideas entry, or control order covers the CLAUDE.md architecture-line
drift — the flag1-snapshot-ingest card updated `docs/current-state.md`
only, and the kit-upgrade cards touched template deltas, not this slot.

## ⟲ Previous-session review

The `2026-07-14-verdict-056-stale-citation` card (this lane's previous
slice) keeps its promises checkable: it predicted "zero test deltas" as
a falsifiable claim and the close-out confirms the identical 575+1
count, and its 💡 is a real find — the three hand-synced copies of the
now-measured 180 (views.py constant, app.js fallback literals, contract
prose) with a concrete parity-test recipe, correctly deduped against
the idea-engine shared-constant idea which covers only schema fields.
Honest nit: the card claims the verdict's boundaries were kept
"verbatim-honest", and they were — including the source's ambiguous
jitter notation "±5/+15 s", copied into the contract without flagging
that the source notation is unresolvable (is the first width ±5 or
−5/+15 asymmetric?). Verbatim fidelity and reader clarity pulled apart
there, and the card should have named the ambiguity so a future
calibration pass (the verdict's own one-day push-timestamp log) knows
to pin it.

- **📊 Model:** fable-5 · medium · docs-only — ingest-transport spec addendum — FLAG-1 sender/receiver seam recorded in the READ contract doc
