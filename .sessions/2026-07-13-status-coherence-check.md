# Session — 2026-07-13 — HTTP-status ↔ reason_code coherence on relayed envelopes

> **Status:** `complete`
> **Branch:** `claude/status-coherence-check`
> **Venue:** lane worker session (coordinator green-light wave — generative
> rung: decide-and-flag, CI-green).

**Goal:** land the second recorded follow-up from PR #60's decide-and-flag
record (`.sessions/2026-07-13-write-path-hardening.md`: "NOT enforced (and
flagged in the PR): the prose HTTP-status↔reason_code mapping table — a
conformant envelope under a mismatched status still relays"). Before this
slice `_serve_action` (server/app.py) relayed any schema-CONFORMANT executor
envelope verbatim even when the HTTP status contradicted the envelope's
content (`ok` under a 4xx/5xx, a rejection reason_code under 200).

Baseline measured on base main @ 5a14f03 (PR #68's serve helper present):
**522 passed + 1 skipped**.

## Close-out

Shipped on `claude/status-coherence-check` (base: main @ 5a14f03). No scope
cut.

**Rules derived, nothing invented:** the contract's "HTTP status mapping"
table (docs/mining-write-contract.md § Response envelope) pairs each of the
13 reason_codes in the CLOSED taxonomy with exactly one status — `ok`⇔200,
`malformed_request`/`unsupported_contract_version`/`unknown_action`/
`invalid_params`⇔400, `invalid_signature`/`stale_timestamp`⇔401,
`guild_not_allowed`⇔403, `actor_not_found`⇔404, `replayed_action`⇔409,
`economy_rejection`⇔422, `rate_limited`⇔429, `internal_error`⇔500. The
schema's reason_code enum is exactly those 13 codes, so the mapping is
TOTAL: the check is `EXPECTED_HTTP_STATUS[reason_code] == status`, full
stop. Replays need no extra rule — "An idempotent replay repeats the
original response's HTTP status", and the original obeyed the table, so
`replayed` never changes the expected row (pinned by test for stored
accepts and stored rejections).

**Left unchecked as unspecified/out-of-layer (one line each):**
- `Retry-After` on 429 — a HEADER expectation, not a status↔reason_code
  pairing; today the relay drops executor headers entirely (see 💡).
- "Replay repeats the ORIGINAL status" as a cross-request property — the
  web server is contractually stateless and cannot compare against a
  stored original; the per-response table row gives equivalent coverage.
- Placeholder `action_id` semantics — the contract attaches no status
  implication beyond the reason_code already checked.

**Wiring:** `server/response_validation.py` gained `EXPECTED_HTTP_STATUS`
(the table, transcribed verbatim) and an opt-in `http_status` kwarg on
`envelope_error` — coherence runs only AFTER schema conformance passes
(schema verdict wins; the jsonschema agreement sweep is untouched — it
judges bodies alone and knows nothing of HTTP). `_serve_action` passes the
executor's status; an incoherent pair draws the existing honest
`502 {"error": "invalid executor response"}`, distinct as before from the
unreachable/timeout 502. Drift guard both ways: CI pins the table's keys
to the schema's reason_code enum, and at runtime a code missing from the
table refuses relay loudly rather than silently skipping the check.

**Shim finding: none.** Audited every `_response`/`_reject_audited` call in
`tests/shim/shim_bot.py` — all 11 emitted pairings sit on the table
(200/ok, 400×4, 401×2, 403, 404, 409, 422); replay returns the stored
original status. The reference impl was already coherent; its runtime pin
(`test_shim_responses_conform_at_runtime`) now also asserts coherence with
the status the shim chose. No shim change.

Coverage (+17 tests, suite **539 passed + 1 skip**):
`tests/test_response_validation.py` — table⇔schema-enum equality pin, an
exhaustive 13×7 sweep (every reason_code passes under exactly its table
status, refused under every other), replay-repeats-the-row pin,
omitted-http_status stays schema-only, conformance-verdict-wins,
table-drift-fails-loud (via the schema injection seam).
`tests/test_actions.py` — end-to-end through the real relay: seven
incoherent classes (ok under 500/409, ok-replay under 502, rejection under
200, key-reuse under 422, rate-limited under 200, internal-error under
400) → the distinct 502; four coherent pairs (accepted replay 200,
economy_rejection 422, rate_limited 429, internal_error 500) relay
verbatim, error statuses included. Contract prose (§ Web session → suid
binding) now names the coherence layer; Status badge untouched in the
first 12 lines.

ORDER-038 note: no cross-agent reviewer reply was received or acted on in
this slice; if one lands on the PR, verify its cited line ranges against
EOF at the reviewed head before acting.

## 💡 Session idea

The coherence work surfaced a real contract gap one layer up: the contract
says a 429 carries a `Retry-After` header (integer seconds), but
`server/actions.py::propose` returns only `(status, body)` —
`res.headers` / `err.headers` are dropped on the floor — and
`_serve_action` sets only its own Content-Type/Length/Cache-Control, so a
relayed `rate_limited` rejection reaches the browser WITHOUT the header
the contract promises clients. Guard recipe: have `propose` also return
the executor's `Retry-After` value (just that one header, not a general
header relay), forward it in `_serve_action` iff present on a 429, and pin
with a fake-executor test (429 + `Retry-After: 7` → browser sees 7;
non-429 never grows the header). Decide-and-flag candidate: whether a 429
MISSING the header should count as incoherent (the contract says "plus a
Retry-After header") or stay advisory.

## ⟲ Previous-session review

The `2026-07-13-serve-helper-dedupe` card is the most spot-check-clean of
the dedupe run. Its close-out claims all reproduced at this session's
HEAD: "522 passed + 1 skipped" was tonight's measured baseline verbatim
on 5a14f03; the conftest `serve` fixture and `tests/_server_helpers.py`
are byte-real; test_server_robustness's documented divergent fixture is
still there shadowing the conftest name. Its 💡 (a `run_server(server)`
lifecycle contextmanager over seven remaining thread-start/teardown
copies) spot-checked accurate at three of the cited sites —
tests/conftest.py:55's `base_url`, and tests/test_readiness.py:112/151/178
all carry the exact `Thread(target=server.serve_forever, daemon=True)`
boilerplate claimed — and the recipe's discipline (lifecycle only,
constructors and yield shapes stay local) is the right cut; still
unlanded, still a good quiet-slot micro-slice. One soft ding: its ⟲
carried forward the records-pass escalation ("land the bare-📊-line sweep
or drop it in one line") for the sixth review running, and this card must
do the same — the escalation is now older than half the ledger; next
records session should treat "drop it in one line" as the default. This
is again a code slice, not a records session, so: carried, un-softened.

- **📊 Model:** fable-5 · standard effort · task-class: PR #60 flagged follow-up — HTTP-status↔reason_code coherence layer on relayed executor envelopes (build)
