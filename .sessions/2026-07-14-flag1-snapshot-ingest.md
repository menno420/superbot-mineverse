# Session — 2026-07-14 — FLAG-1 snapshot-ingest RECEIVE endpoint

> **Status:** `complete`
> **Branch:** `claude/flag1-snapshot-ingest`
> **Venue:** lane worker session (ORDER 006 item 1 — EAP final-night
> worklist; ORDER 007 production-grade doctrine adopted: correctness
> outranks speed, no gate relaxed).

**Goal:** build the FLAG-1 snapshot-ingest RECEIVE endpoint that
ORDER 006 item 1 names: superbot PR #2058 POSTs a v1 snapshot to
`MINING_SNAPSHOT_RELAY_URL` every ~60 s, but `server/app.py` `do_POST`
handles only `/api/action` — the receiving endpoint exists nowhere.
Ship: HMAC-verified `POST /api/snapshot/ingest` (reusing the repo's ONE
canonical signing scheme, `server/actions.py` `sign`/`verify` —
`X-Mineverse-Signature`/`X-Mineverse-Timestamp`, HMAC-SHA256 over
`METHOD\nPATH\nTIMESTAMP\nsha256(body)`, ±300 s skew, constant-time) →
v1-validate with the existing runtime validator
(`server/snapshot_validation.py`) BEFORE anything persists → atomic
whole-document replace into the `MINING_SNAPSHOT_PATH` file the read
seam already re-reads fresh per request. Secret from
`MINING_SNAPSHOT_RELAY_SHARED_SECRET` (host env, never the repo);
secret or path unset → fail closed (honest 503, unsigned data never
accepted). Full test coverage in the repo's existing HTTP-seam style;
stdlib-only prod path; docs ledger kept truthful. The item-3
spec addendum to `docs/mining-data-contract.md` is the NEXT slice —
this card records the facts it needs.

## Close-out

Shipped on `claude/flag1-snapshot-ingest` (base: main @ `de3325c`, after
the #87 claim merge). New `server/ingest.py` — `IngestConfig`
(`from_env`, `or None` empty-string-is-unset convention shared with
`WriteConfig`/`snapshot_path_from_env`; `configured` iff BOTH secret and
path) + `persist_snapshot` (same-directory `mkstemp` → write → flush →
fsync → `os.replace`; parent dir deliberately never created — host
provisions it, a missing dir is the caller's honest 500). The canonical
`MINING_SNAPSHOT_PATH` constant moved to `ingest.py`; `app.py` aliases
it so existing importers are untouched.

`server/app.py`: `POST /api/snapshot/ingest` (`_serve_snapshot_ingest`)
with the check order documented in its docstring — fail-closed 503
unconfigured (no unsigned mode, no built-in secret, committed sample
never a write target) → body bounds BEFORE the read (400 bad length,
413 over 1 MiB) → transport auth over the RAW bytes via `actions.verify`
(the one canonical scheme; constant-time; signature before the ±300 s
window; 401 `invalid_signature`/`stale_timestamp`) → 415 non-JSON
content type → 400 malformed JSON → 400 v1-contract violation (same
runtime validator the read side re-checks per request; logged) → atomic
persist → `200 {"status": "accepted"}`. Wrong verbs on the route answer
405 `Allow: POST` via the new `POST_ONLY_API_ROUTES` set (shared with
`/api/action`). Ordering is last-write-wins, replaced whole — the
contract defines the relay as "the latest document" from a single 60 s
no-retry sender; a replay inside the skew window rewrites identical
bytes (idempotent by content). `main()` now prints the ingest mode line
alongside sign-in/writes/snapshot.

**Ingest-auth decision (evidence trail, for the item-3 addendum):**
#2058's body names NO transport auth ("FLAG 1 names no transport"), so
the receive side set the scheme fail-closed rather than accept unsigned
data: the repo's canonical Mineverse HMAC scheme, already implemented on
both sides of FLAG 2. Env NAME composed from evidence: #2058's
`MINING_SNAPSHOT_RELAY_*` prefix × the write contract's
`*_SHARED_SECRET` suffix → `MINING_SNAPSHOT_RELAY_SHARED_SECRET`.
Persist target reuses `MINING_SNAPSHOT_PATH` (the consume seam from the
2026-07-13 ingestion-seam card) so an accepted push is served on the
very next per-request fresh read with zero new read-side code.

Verified pre-flip in this container: `python3 -m pytest -q` →
**575 passed, 1 skipped** (baseline 551 + 24 new in
`tests/test_snapshot_ingest.py`: accept + read-route round-trip,
replace-whole, unsigned/bad-key/wrong-path/tampered-body/stale-timestamp
401s that never persist, the fail-closed matrix incl. the pure
`from_env` default path, schema/JSON/content-type/oversize/verb
rejections, config + persist units). `docs/current-state.md` updated
(degraded-by-default names, FLAG-1 pending bullet, shipped line).
Item 5's readiness/cutover extension and item 3's contract addendum are
deliberately NOT here — next slices.

## 💡 Session idea

`server/app.py` now parses `Content-Length` + bounds-checks + reads the
body in two hand-rolled copies (`_read_action_request` at
`MAX_ACTION_BODY_BYTES`, `_serve_snapshot_ingest` at
`ingest.MAX_SNAPSHOT_BODY_BYTES`) — a third POST route would copy it
again, and the copies already differ subtly: the action path folds every
length problem into one 400, the ingest path distinguishes 400/413 and
answers BEFORE draining, which this session's own test run showed gives
the CLIENT a broken pipe instead of the 413 when the body is large
(test pins it via a raw http.client partial send). Guard recipe: extract
one `_read_bounded_body(self, max_bytes) -> bytes | None` helper (parse +
bounds + read + the answer-then-close semantics, e.g. a `Connection:
close` header on pre-drain rejections so the refusal is deterministic
for real senders), collapse both sites onto it, verified by
`tests/test_actions.py`'s oversize/garbage-length cases and
`tests/test_snapshot_ingest.py`'s 400/413 cases staying green. Dedup
checked: the server-internals-dedupe card collapsed the snapshot LOAD
paths, the ingestion-seam card's idea was the same load-block dedupe —
no card or ideas doc covers the request-BODY read path.

## ⟲ Previous-session review

The `2026-07-13-docs-kit-v1150-deltas` card is a strong docs-slice
close-out: its scope boundary (template structure only, every
host-specific finding survives) is stated as a checkable claim and the
close-out then actually checks it ("zero removed ledger lines in the
diff", append-log entries counted), and the three-way archaeology it had
to do — report vs live file vs two sibling repos — is exactly the
re-derivation cost its 💡 (`bootstrap.py upgrade --remaining-docs`)
would delete; that idea is kit-lab material and still unlanded, worth an
outbox relay if a records pass has a quiet slot. Honest nit it earns:
it names the born-red interim rule implicitly (verified strict red "with
ONLY the designed hold") but, like this session, still cannot arm a real
hold for a single-PR session — the upstream gate fix the 2026-07-12
finding routed out remains the only real cure, and cards keep paying the
verification-narration tax until it lands.

- **📊 Model:** fable-5 · standard effort · task-class: FLAG-1 snapshot-ingest RECEIVE endpoint — HMAC-verified POST → v1-validate → atomic persist (build)
