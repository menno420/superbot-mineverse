"""FLAG-1 snapshot-ingest RECEIVE seam — stdlib-only, degraded by default.

This module is the receive half of the bot→web READ relay (FLAG 1 in
``control/status.md``). The bot side (superbot PR #2058) POSTs the v1
mining snapshot to the URL in its ``MINING_SNAPSHOT_RELAY_URL`` env var
every ~60 s (contract cadence — docs/mining-data-contract.md § "Delivery
expectations"; 10 s timeout, failures logged bot-side and absorbed, no
retry). ``POST /api/snapshot/ingest`` (``server/app.py``) is the endpoint
that URL should name; this module holds its host-env configuration and
the one persistence primitive.

Configuration comes from HOST environment variables ONLY (never files,
never the repo):

- ``MINING_SNAPSHOT_RELAY_SHARED_SECRET`` — HMAC-SHA256 key the sender
  signs with. #2058's body names no transport auth ("FLAG 1 names no
  transport"), so the receive side sets the scheme FAIL-CLOSED: the repo's
  ONE canonical Mineverse signing scheme (``server/actions.py``
  ``sign``/``verify`` — ``X-Mineverse-Signature`` /
  ``X-Mineverse-Timestamp``, HMAC-SHA256 over
  ``METHOD\\nPATH\\nTIMESTAMP\\nsha256_hex(BODY)``, constant-time compare,
  ±300 s skew). The env NAME composes #2058's ``MINING_SNAPSHOT_RELAY_*``
  prefix with the write contract's ``*_SHARED_SECRET`` suffix
  (``MINING_WRITE_SHARED_SECRET``).
- ``MINING_SNAPSHOT_PATH`` — the persist target: the SAME live-feed file
  the read seam (``server/app.py`` ``snapshot_path_from_env``) already
  re-reads fresh and v1-validates on every request, so an accepted
  snapshot is served on the very next read with zero new read-side code.

With either absent the app runs in DEGRADED MODE, exactly like the OAuth
and write vars: the endpoint answers an honest ``503 {"error": "snapshot
ingest not configured"}`` and NEVER accepts data — there is no unsigned
mode and no built-in secret. In particular, with ``MINING_SNAPSHOT_PATH``
unset the endpoint must stay closed: accepting would mean writing over
the committed sample (``data/sample_snapshot.json``), which is repo data,
not relay state.

Persistence honors the contract's atomicity clause ("a snapshot is
replaced whole, never patched; a reader never observes a half-written
document"): same-directory temp file + fsync + ``os.replace``.
Ordering is last-write-wins — the contract defines the relay as "the
latest document" from a single 60 s-cadence sender with no retry, so
there is no cross-request ordering to arbitrate; replaying a captured
signed request inside the ±300 s skew window rewrites the identical
bytes (idempotent by content).
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

ENV_INGEST_SECRET = "MINING_SNAPSHOT_RELAY_SHARED_SECRET"
# The canonical home of the snapshot-path env name (the read seam in
# server/app.py aliases this constant): one string, two consumers, no drift.
ENV_SNAPSHOT_PATH = "MINING_SNAPSHOT_PATH"

# One guild's miners at v1 shapes is a few KiB; 1 MiB is generous headroom
# without letting an unauthenticated client stream us an unbounded body
# (the size check runs BEFORE the body is read or verified).
MAX_SNAPSHOT_BODY_BYTES = 1024 * 1024


class IngestConfig:
    """Ingest-endpoint configuration snapshot. ``None`` values = degraded."""

    def __init__(self, secret: str | None, path: Path | None) -> None:
        self.secret = secret
        self.path = path

    @classmethod
    def from_env(cls, environ=os.environ) -> "IngestConfig":
        """Empty string counts as UNSET (the ``or None`` convention shared
        with ``actions.WriteConfig.from_env`` / ``snapshot_path_from_env``)."""
        secret = environ.get(ENV_INGEST_SECRET) or None
        configured_path = environ.get(ENV_SNAPSHOT_PATH) or None
        return cls(secret=secret, path=Path(configured_path) if configured_path else None)

    @property
    def configured(self) -> bool:
        return bool(self.secret and self.path)


def persist_snapshot(path: Path, payload: bytes) -> None:
    """Atomically replace ``path`` with ``payload`` — whole, never patched.

    Same-directory temp file + flush + fsync + ``os.replace`` so a reader
    (the per-request fresh read in ``server/app.py``) can never observe a
    half-written document (docs/mining-data-contract.md § "Atomicity").
    The parent directory is HOST-provisioned alongside the env var and is
    deliberately not created here — a missing directory is a configuration
    error and surfaces as the caller's honest 500, never a silent mkdir.
    Raises ``OSError`` on any filesystem failure; the temp file is cleaned
    up on the way out.
    """
    fd, tmp_name = tempfile.mkstemp(
        dir=str(path.parent), prefix=path.name + ".", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "wb") as tmp:
            tmp.write(payload)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
