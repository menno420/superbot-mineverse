# Session 2026-07-14 — shared bounded POST-body reader

> **Status:** `complete`

## Plan

Improvement-wave lane H, PR 2 of 3 (owner directive 2026-07-14; claim
PR #95). Land the guard recipe from the 2026-07-14-flag1-snapshot-ingest
card's 💡: `server/app.py` parses Content-Length + bounds-checks + reads
the POST body in two hand-rolled copies (`_read_action_request` at
`MAX_ACTION_BODY_BYTES`, `_serve_snapshot_ingest` at
`ingest.MAX_SNAPSHOT_BODY_BYTES`). Extract ONE shared bounded-body
reader parameterized on max-bytes + error emission, PRESERVING every
observable behavior: the action path's single folded 400, the ingest
path's 400-vs-413 distinction, header order, and the answer-before-drain
broken-pipe behavior the ingest card pins. Pure refactor — the existing
action + ingest test gauntlets must pass UNCHANGED.

## Close-out

- `server/app.py` (+49/−22, the ONLY file changed besides this card):
  new `_read_bounded_body(self, max_bytes, *, errors=None) -> bytes |
  None` beside `_read_action_request` — parse `Content-Length`,
  bounds-check BEFORE reading a byte, read exactly `length` bytes. The
  two hand-rolled copies collapse onto it:
  - `_read_action_request` calls it in QUIET mode (`errors=None`): any
    length problem (bogus header, non-positive, over
    `MAX_ACTION_BODY_BYTES`) or read failure returns None and the
    caller's single folded 400 stands, exactly as before. `json.loads`
    now parses the returned bytes; the old combined
    `except (OSError, ValueError)` split cleanly (OSError caught in the
    helper, ValueError at the parse) with identical outcomes.
  - `_serve_snapshot_ingest` calls it in EMITTING mode
    (`errors=("invalid content length", "snapshot too large")`): the
    400-vs-413 distinction, the exact error strings, header order (same
    `_send_json`), and the answer-before-drain broken-pipe behavior the
    flag1 card pins all preserved; read failure still answers nothing.
- Deliberately NOT taken: the flag1 💡's optional `Connection: close`
  header on pre-drain rejections — that would CHANGE observable bytes,
  and this slice's bar was byte-identical responses.
- Zero test edits (not even imports): `tests/test_actions.py` +
  `tests/test_snapshot_ingest.py` gauntlets pass unchanged
  (91 passed, 1 skipped together).
- verify: `python3 -m pytest -q` → `598 passed, 1 skipped` (same as the
  post-#99/#100 baseline — a pure refactor adds nothing); `python3
  bootstrap.py check --strict` → exit 0.

## 💡 Session idea

`_read_bounded_body`'s emitting mode hard-codes status 400/413 and the
caller supplies only the strings. If a third POST route ever needs a
different status taxonomy (e.g. a 411 for absent length, per RFC), the
`errors` tuple becomes a lie to extend — at that point promote it to a
small mapping (`{"bad_length": (400, msg), "too_large": (413, msg)}`)
rather than adding positional fields. Not worth it at two callers.
(Deduped: the flag1 card's reader-dedupe 💡 is DONE here and retired;
its optional Connection-close refinement remains open and is now the
only unlanded part — noted above as deliberately out of scope.)

## ⟲ Previous-session review

The 2026-07-14-flag1-snapshot-ingest card's 💡 is a model guard recipe:
it named the exact helper signature, both call sites, the subtle
behavioral differences (folded 400 vs 400/413, answer-before-drain),
and the two test gauntlets that must stay green — this session landed
it in one pass with zero re-derivation. One honest correction: the
recipe's suggested signature bundled the `Connection: close` refinement
into the extraction, but that half is a behavior CHANGE and the
extraction half is a pure refactor — splitting them (as done here)
keeps the refactor's "tests pass unchanged" bar crisp. Its prediction
that "a third POST route would copy it again" is now structurally
prevented rather than merely warned about.

- **📊 Model:** fable-5 · standard effort · task-class: bounded POST-body reader dedupe — pure refactor, byte-identical responses (refactor)
