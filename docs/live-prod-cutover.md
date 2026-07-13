# superbot-mineverse — LIVE-PROD cutover checklist (stage d prep) — OWNER-FLAG-GATED

> **Status:** `binding`
>
> The owner-gated path from test-guild writes (stage c, shipped) to live
> production guilds (stage d, NOT shipped). This document prepares the flag;
> it does not throw it. **Nothing here enables, defaults, or shortcuts any
> live-prod write path** — the WRITE contract's TEST-GUILD-ONLY wall
> (docs/mining-write-contract.md § "TEST GUILD ONLY") stays up until the
> owner flips it per § "THE FLAG ITSELF" below. Mechanical twin:
> `scripts/readiness_check.py` (§6). Where this doc and the contract
> disagree, the contract wins.

## 1. Prerequisites — all boxes checked before the flag is even discussable

Each item carries its evidence — a command or a concrete observation. An
unchecked box anywhere on this list means stage d does not start.

- [ ] **The real bot-side endpoint exists and passes the contract fixtures
  against the TEST guild.** The done-criterion from
  docs/mining-write-contract.md § "Enforcement": the shim's contract tests
  validate against the real endpoint's behavior. The seam is an opt-in
  env-var switch inside `tests/test_actions.py` — no hand-edit, ever: when
  `SHIM_CONFORMANCE_BASE_URL` is set, the `shim` fixture yields that base
  URL instead of booting the in-process shim, and the SAME contract
  fixtures run against the real endpoint. The signing secret comes from
  `MINING_WRITE_SHARED_SECRET` (the contract's canonical env name — the
  same value the executor verifies with), overridable with
  `SHIM_CONFORMANCE_SECRET` when the shell already carries a web-host
  secret that differs from the conformance target's. Values are exported
  in the shell only — never files, never printed.
  *Evidence:*

  ```
  SHIM_CONFORMANCE_BASE_URL=https://<real-endpoint-host> \
  MINING_WRITE_SHARED_SECRET=<the test-guild secret> \
  python3 -m pytest tests/test_actions.py -q
  ```

  run against a test guild freshly loaded with `data/sample_snapshot.json`
  — the conformance sweep must be green. Fine print: the base URL is
  scheme + host(+port) only (the tests append `/relay/mining/action`);
  assertions on the shim's in-memory `state` (audit rows, executed-once
  evidence) guard or skip themselves in this mode — audit verification
  against the real endpoint stays the manual checklist item below; the
  deterministic-delta assertions assume the committed snapshot's starting
  values, so reload the fixture data between passes. With the env vars
  unset (CI, fresh clones) the suite is hermetic and the
  conformance-vs-real-endpoint smoke test skips with an honest reason —
  CI never needs a secret. One-command wrapper for this whole sweep
  (env check + unsigned probe + pytest + PASS/FAIL verdict):
  `python3 scripts/conformance_run.py` — one-page runbook:
  `docs/conformance-runbook.md`.
- [ ] **pytest is a required (blocking) status check on main's ruleset.**
  This is an OPEN OWNER ASK — carried in `control/status.md` as
  ⚑ OWNER-ACTION 2 since stage b. Today only `substrate-gate` is required;
  the `pytest` context (from `.github/workflows/schema-gate.yml`) is
  advisory, so a red test suite can still merge. Live-prod traffic must not
  sit behind an advisory test gate.
  *Evidence:* Settings → Rules → Rulesets → main ruleset lists required
  context `pytest`; the next merged PR's check runs show pytest completed
  before merge.
- [ ] **All six host env vars are provisioned on the web host** (names
  below; values live only in the host environment — never in this repo,
  never in a file, never printed):
  `DISCORD_OAUTH_CLIENT_ID`, `DISCORD_OAUTH_CLIENT_SECRET`,
  `OAUTH_REDIRECT_URI`, `WEB_SESSION_SIGNING_KEY` (docs/auth.md),
  `MINING_WRITE_ENDPOINT`, `MINING_WRITE_SHARED_SECRET`
  (docs/mining-write-contract.md § "Degraded mode").
  *Evidence:* `python3 scripts/readiness_check.py` on the web host exits 0
  and reports all six SET. The script prints SET/UNSET only — never a
  value (§6). (Related but NOT one of the six: `MINING_SNAPSHOT_PATH` —
  the READ-relay consume seam. It is optional at every stage — unset, the
  server serves the committed sample — so it is not a write-flag
  prerequisite and the readiness check does not require it; a live read
  feed additionally wants it pointed at the bot relay's snapshot file.)
- [ ] **The OAuth redirect URI is registered in the Discord developer
  app** and byte-equals the host's `OAUTH_REDIRECT_URI` (an `https://`
  value also turns on the session cookie's `Secure` flag — docs/auth.md).
  *Evidence:* Discord Developer Portal → the app → OAuth2 → Redirects
  lists exactly the `/auth/callback` URL the host serves; a real
  `/auth/login` round-trip lands back signed in instead of on a Discord
  "invalid redirect" page.
- [ ] **The audit trail is verified end to end in the TEST guild.** The
  binding requirement (docs/mining-write-contract.md § "AUDIT
  REQUIREMENT"): every web-originated action — accepted or rejected —
  produces one audit record with `action_id`, `action`, `suid`,
  `guild_id`, `params_digest`, `outcome`, `timestamp`,
  `contract_version: "1"`, `origin: "web"`.
  *Evidence, concretely:* signed into the test-guild site, perform (a) an
  accepted `mine`, (b) an economy rejection (e.g. `sell` more than the
  inventory holds → 422 `economy_rejection`), and (c) a byte-identical
  retry of (a) (same `action_id`). Then read the bot-side audit store and
  confirm: (a) and (b) each produced exactly one row with the fields
  above and the row's `suid` equals the signed-in Discord user id; (c)
  produced NO new row (idempotent replays are not re-audited) and the
  response carried `replayed: true`. The shim's in-memory log
  (`tests/shim/shim_bot.py`, asserted in `tests/test_actions.py`) is the
  reference shape for the rows.

## 2. Rate-limits review — contract defaults vs prod population

The contract's executor-side budgets, per `(suid, guild_id)`
(docs/mining-write-contract.md § "Rate limits"):

- **Burst:** 10 actions per 10 seconds.
- **Sustained:** 60 actions per minute.

Review before the flag:

- [ ] **Do the math against real player counts.** The limits are
  per-player, so total endpoint load scales linearly with concurrently
  active players: N active players can legally deliver up to 60·N
  proposals/minute. Confirm the bot host's endpoint (and its Postgres
  write path through `disbot/services/mining_workflow.py`) is sized for
  the prod guilds' expected concurrency, not the test guild's.
- [ ] **Consider tightening for prod.** 60/min sustained is a generous
  dev-era budget — a human clicking the web UI rarely exceeds ~10–20
  actions/min. A prod-day tightening (e.g. 30/min sustained, keep 10/10 s
  burst) is executor-side configuration and needs no contract change: the
  contract calls the numbers "executor-configurable" expectations. Any
  change to the *documented defaults* is a contract edit in this repo
  first.
- [ ] **Know where enforcement lives.** Enforcement is bot-side
  (executor) ONLY — over budget answers HTTP 429,
  `reason_code: "rate_limited"`, with a `Retry-After` header in seconds,
  and rate-limited proposals are NOT stored for idempotency. The web
  server relays that envelope verbatim (`server/app.py` `_serve_action`);
  the web UI (`web/app.js` `showActionResult`) surfaces it as an error
  line (`✗ rate_limited: <message>`) and does NOT auto-retry — the player
  must click again. There is no web-side throttle to tune and none should
  be added silently (client-side throttling would only mask executor
  telemetry).

## 3. Abuse review — what can go wrong, what we do about it

- [ ] **Session-cookie theft.** The `mineverse_session` cookie
  (docs/auth.md) is HMAC-SHA256-signed, `HttpOnly` (no script access),
  `SameSite=Lax`, `Secure` under an https redirect URI, 7-day expiry. A
  stolen cookie lets the thief act as that ONE player in the game economy
  until expiry — it carries no Discord access token and nothing replayable
  against Discord. **Rotation procedure:** replace
  `WEB_SESSION_SIGNING_KEY` on the web host and restart the server.
  Effect: every outstanding session cookie (and any in-flight OAuth
  `state` token) fails verification immediately — all users are signed
  out and must re-authenticate; nothing else changes. This is the cheap,
  always-safe first response to any suspected session compromise.
- [ ] **CSRF posture.** What the code actually does: the OAuth callback
  is CSRF-protected by the HMAC-signed, 10-minute-expiring `state` token
  (`server/auth.py`, verified before the code is touched). For
  `POST /api/action` there is no per-request CSRF token; the standing
  defenses are `SameSite=Lax` on the session cookie (a cross-site POST
  does not carry it) plus the strict body shape — `_read_action_request`
  in `server/app.py` accepts exactly the three keys
  `{action_id, action, params}` and rejects everything else. A
  cross-site attacker without the cookie gets `401 sign-in required`.
  If prod review wants belt-and-suspenders, an `Origin`-header check on
  `POST /api/action` is a small additive change — note it as a candidate,
  do not ship it inside the cutover.
- [ ] **Replay / idempotency abuse.** `action_id` is the idempotency key
  (docs/mining-write-contract.md § "Idempotency"): a byte-identical retry
  returns the ORIGINAL response with `replayed: true` and never
  re-executes; reusing an `action_id` with a different body is rejected
  `replayed_action` (409) and IS audited (a client anomaly worth seeing).
  Resubmitting a captured signed proposal therefore cannot double-execute
  inside the ≥24 h retention window, and the ±300 s signature skew window
  (`server/actions.py`, `SKEW_SECONDS = 300`) kills replays of captured
  transport signatures after five minutes anyway.
- [ ] **Action spam.** Bounded by the per-(suid, guild) executor rate
  limits (§2) — spam costs the spammer their own budget only. The web
  relay also caps request bodies at 64 KiB (`MAX_ACTION_BODY_BYTES`,
  `server/app.py`) and requires a verified session before anything is
  relayed, so anonymous spam never reaches the executor. Watch the audit
  log for `rejected:rate_limited`-adjacent patterns and `replayed_action`
  rows during the observation window (§5).
- [ ] **suid spoofing — impossible by construction (verify, then trust).**
  The browser body may contain ONLY `{action_id, action, params}`;
  `_read_action_request` (`server/app.py`) rejects any body whose key set
  differs — a body carrying `suid` or `guild_id` is a 400 before anything
  is relayed. `suid` is set server-side from the VERIFIED session cookie
  (`user_id = self._session_user_id(...)`; cookie verification is
  constant-time HMAC in `server/auth.py`) and `guild_id` comes from the
  committed snapshot envelope. There is no code path by which browser
  input reaches the identity fields of the proposal —
  `tests/test_actions.py::test_browser_cannot_assert_suid_or_guild` pins
  this. An attacker can act as a player only by holding that player's
  valid signed cookie (see cookie theft above), never by asserting a
  suid.
- [ ] **`MINING_WRITE_SHARED_SECRET` compromise.** An attacker holding
  the shared secret (and knowing the endpoint URL) can sign arbitrary
  proposals directly to the bot-side endpoint — as ANY suid in ANY
  allowlisted guild, bypassing the web server's session binding entirely.
  The blast radius is still bounded by the executor: closed action enum,
  schema validation, guild allowlist, per-(suid, guild) rate limits, and
  the audit requirement (rows with `origin: "web"` the real web server
  never sent are the detection signal). **Rotation procedure — order of
  operations:** (1) generate a new secret; (2) install it on the BOT host
  and restart/reload the executor first (if the executor can briefly
  accept old+new, use that grace window); (3) install it on the WEB host
  (`MINING_WRITE_SHARED_SECRET`) and restart the web server; (4) confirm
  a signed-in test action round-trips (200 `ok`); (5) destroy the old
  secret. Between (2) and (3) web-originated actions fail honestly with
  `invalid_signature` (401) — a short, visible outage, never a silent
  acceptance of the old key. If compromise is suspected mid-rotation,
  invert the availability trade: shrink the bot-side allowlist to empty
  first, then rotate.

## 4. Rollback — instant degrade paths, and who pulls which lever

The system is degraded-by-default at every layer; rollback is unsetting
things, never deploying things.

| Lever | Action | Effect | Who |
|---|---|---|---|
| Kill the live snapshot feed | Unset `MINING_SNAPSHOT_PATH` on the web host, restart | The read routes go back to serving the committed sample (`data/sample_snapshot.json`) — demo data, honestly static. While the var stays SET, a missing/invalid feed file already answers `503 {"error": "snapshot unavailable"}` per request (no last-good cache, no silent fallback), so this lever is for *choosing* the sample over an outage page. | Owner (host env) |
| Kill writes | Unset `MINING_WRITE_ENDPOINT` (or `MINING_WRITE_SHARED_SECRET`) on the web host, restart | `WriteConfig.configured` goes false (`server/actions.py`): `POST /api/action` answers `503 {"error": "writes not configured"}`, `/api/me` reports `writes_configured: false`, the UI disables every action button with the honest "Writes not configured — read-only mode" tooltip. Reads untouched. | Owner (host env) |
| Kill sign-in too | Also unset the four OAuth vars (docs/auth.md), restart | Read-only PUBLIC site: `/api/me` → `signed_in: false, auth_configured: false`, `/auth/login` → 503. The snapshot views keep working for everyone. | Owner (host env) |
| Kill one guild / all guilds | Shrink the bot-side allowlist (remove the prod guild id(s)) | Executor rejects that guild's proposals with `guild_not_allowed` (403) — the web UI shows the rejection honestly; no web-side change needed. The surgical lever: one guild can be rolled back while others stay live. | Owner (bot host) |
| Sign everyone out | Rotate `WEB_SESSION_SIGNING_KEY`, restart | All session cookies invalid at once (§3). Use when sessions, not the write path, are the problem. | Owner (host env) |
| Incident review | Pull the audit rows for the window (`origin: "web"`, filter by guild/suid/outcome) | Every web-originated action — accepted or rejected — has a row (§1 audit prerequisite), so "what happened" is a query, not a reconstruction. | Owner pulls data; agent sessions analyze and write up |

Lanes: every lever above lives on hosts and consoles only the owner
touches — agent sessions have no host access by design. The agent lane's
rollback contribution is preparation (this doc, the readiness script,
test coverage) and post-incident analysis via PRs; no agent action is on
any rollback critical path.

## 5. THE FLAG ITSELF — owner-only, two explicit acts, never an agent

> **LIVE PROD TURNS ON ONLY WHEN THE OWNER (menno420) DOES BOTH OF:**
>
> **(a)** adds the production guild id(s) to the BOT-SIDE allowlist
> (the hard allowlist the executor holds —
> docs/mining-write-contract.md § "TEST GUILD ONLY"), **and**
>
> **(b)** says so explicitly — a `control/inbox.md` ORDER, or an
> equivalent explicit owner statement naming the guild(s) and the go.
>
> **No agent may decide-and-flag this.** Not by editing an allowlist, not
> by widening the schema or the contract, not by inferring "the checklist
> is green so we're go", not by relaying a third party's ask. A checklist
> with every box ticked is a *ready* flag, not a *thrown* flag. Anything
> in this repo that would have the effect of enabling a live-prod write
> path without both owner acts above is a bug and a contract violation
> (docs/mining-write-contract.md: "That flag is the owner's alone;
> nothing in this contract or its implementations may widen the
> allowlist").

Suggested staged rollout (owner's call, sequencing only):

1. **One prod guild first.** Add a single production guild id to the
   allowlist; announce to that guild.
2. **Observation window** (suggest 48–72 h): watch the audit log
   (volume, `outcome` mix, any `replayed_action` or `origin` anomalies)
   and the rate-limit hit rate (429s per player — near-zero expected for
   human play; a hot spot is either a bot or a limit set too tight).
3. **Then the fleet.** Widen the allowlist to the remaining prod guilds
   only after the window looks boring. Boring is the goal.

## 6. Mechanical readiness check — `scripts/readiness_check.py`

The machine-checkable slice of §1, stdlib-only, safe to run anywhere
(CI, a fresh clone, the prod host):

```
python3 scripts/readiness_check.py           # env presence only, no network
python3 scripts/readiness_check.py --probe   # + one unsigned probe of MINING_WRITE_ENDPOINT
```

- **What it checks:** presence of each of the six env vars (§1), printed
  as `SET`/`UNSET` — **never a value, never a prefix, never a length**.
  Exit 0 iff all six are SET (and the probe, when requested, passed);
  exit 1 otherwise, with a plain-language report naming what's missing.
- **`--probe`** (opt-in, only meaningful where `MINING_WRITE_ENDPOINT`
  is set): POSTs one deliberately UNSIGNED empty request to the endpoint
  and expects the contract's pre-auth rejection — HTTP 401,
  `reason_code: "invalid_signature"`, a response envelope carrying the
  contract's required fields (docs/mining-write-contract.md § "Transport
  auth"). Signature-first verification means an unsigned probe can never
  execute anything, is never audited, and learns nothing but "the
  executor is up and speaking contract v1". The probe never sends or
  needs any secret.
- **What it CANNOT check from this repo:** the bot-side allowlist
  contents (owner-held, bot host), the Discord developer app's redirect
  registration, the audit trail's end-to-end behavior (§1's manual
  verification), main's branch-ruleset required checks, whether env var
  VALUES are correct (a SET-but-wrong secret only surfaces as
  `invalid_signature` on a real signed action), and anything about
  hosts it isn't run on — run it ON the web host for the env verdict
  that counts.
- Logic is covered by `tests/test_readiness.py` (injected env dicts, a
  local stub executor for the probe — green with zero env vars, no
  non-loopback network, exactly like CI).
