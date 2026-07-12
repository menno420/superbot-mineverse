# Session — 2026-07-12 — Railway deployability (HOST env + Dockerfile)

> **Status:** `complete`
> **Branch:** `bot/railway-deployability`
> **Venue:** owner-live superbot session (cross-repo; superbot PR #2043 is the session card).
> **📊 Model:** Fable 5 (Claude 5 family)

**Before:** the web host could not deploy — Railway's buildpack auto-detection fails on a
stdlib-only repo (no requirements.txt/pyproject → BUILD_IMAGE dies in <6s, observed live
2026-07-12 on project `superbot-mineverse`), and `main()` hard-bound `127.0.0.1`, which no
container platform can route external traffic to.

**After:** a committed `Dockerfile` (python:3.10-slim, deterministic — no detection
heuristics) and `main()` honours `HOST` (default stays loopback for local dev/tests;
the Dockerfile sets `HOST=0.0.0.0`; Railway injects `PORT`). Two new tests pin both
halves (`tests/test_deploy_binding.py`).

**Deployment state this unblocks:** Railway project `superbot-mineverse`, service `web`,
domain `https://web-production-97636.up.railway.app` — created + provisioned (3 of 6 env
vars: signing key, redirect URI, client id) by the owner-live session, deployed read-only
degraded per docs/live-prod-cutover.md. GitHub-triggered auto-deploys stay blocked until
the owner grants the Railway GitHub App access to this repo (fleet-manager owner-queue
`OQ-RAILWAY-APP-MINEVERSE`); interim deploys are one-shot CLI uploads.

**💡 Session idea:** commit a `scripts/deploy_railway.sh` (CLI one-shot upload with the
env-override `env -u RAILWAY_PROJECT_ID …` guard baked in) so any agent session can
redeploy the web host reproducibly until the GitHub App click lands — the exact incant
was rediscovered by hand today and lives only in a superbot session log otherwise.

**⟲ Previous-session review:** the 2026-07-11 wrap-up/archive-prep session left the repo
in a genuinely adoptable state (clean status ladder, FLAG 1/2 specs carried verbatim) —
this session could act on infra within minutes of cloning. Gap it surfaced: the ladder's
"(d) PREPARED" claim silently assumed a web host existed somewhere; no doc named WHERE
the host runs or that no host had ever been provisioned. Improvement: deployment facts
(platform, project, service, domain, deploy path) now live in this card + the README
deployment note; keep them in one named home (docs/live-prod-cutover.md §1) as they
change.
