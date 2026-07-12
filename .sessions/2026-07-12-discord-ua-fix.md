# Session — 2026-07-12 — Discord token-exchange fix (Cloudflare blocks urllib UA)

> **Status:** `complete`
> **Branch:** `bot/discord-ua-fix`
> **Venue:** owner-live superbot session (cross-repo follow-up; superbot #2043 lineage).
> **📊 Model:** Fable 5 (Claude 5 family)

**Before:** first live sign-in attempt (owner screen recording, ~20:13 local) reached Discord's
consent screen (redirect URI registered correctly, valid client id + secret — pair verified 200
via client_credentials) but the callback answered `502 {"error": "discord token exchange
failed"}`. Root cause isolated live: discord.com (Cloudflare) **403s urllib's default
User-Agent** — the same endpoint answers 200 to a curl UA and 403 to `Python-urllib/3.10`. The
bare `except` swallowed the 403, so the 502 was unexplainable from outside.

**After:** `exchange_code` + `fetch_discord_user` send an explicit `HTTP_USER_AGENT`;
the callback logs the underlying exception to stdout (host runtime logs) while the client
response stays opaque; `test_discord_requests_carry_real_user_agent` pins the header on both
requests and forbids "urllib" in the UA string.

**💡 Session idea:** a tiny `scripts/probe_auth.py --live` (opt-in, no secrets printed) that
runs the client_credentials pair-check + a UA-reachability check against discord.com from the
deploy host — would have turned today's blind 502 into a one-command diagnosis.

**⟲ Previous-session review:** the same-day railway-deployability session shipped a working
host fast, but its "sign-in is one portal click away" claim was over-confident — the OAuth
path had never been exercised end-to-end from the deployed host, and the first real attempt
found this UA wall. Improvement: for any "X is now one step from working" claim, name the
untested leg explicitly (here: the live token exchange) so the owner knows a first-try failure
is expected diagnosis material, not a broken promise.
