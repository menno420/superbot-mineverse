"""Deployment binding: the container host path must accept non-loopback binds.

The Dockerfile sets HOST=0.0.0.0 and Railway injects PORT; main() feeds both
into make_server. These tests pin the two halves: make_server honours an
explicit non-loopback host, and main()'s env plumbing reads HOST/PORT.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from server.app import make_server  # noqa: E402


def test_make_server_binds_all_interfaces():
    server = make_server(host="0.0.0.0", port=0)
    try:
        host, port = server.server_address[:2]
        assert host == "0.0.0.0"
        assert port > 0
    finally:
        server.server_close()


def test_main_reads_host_and_port_env(monkeypatch):
    captured = {}

    class _StubServer:
        server_address = ("0.0.0.0", 8123)

        def serve_forever(self):
            raise KeyboardInterrupt  # main() handles this as clean shutdown

        def shutdown(self):
            pass

    def fake_make_server(host="127.0.0.1", port=0, **kwargs):
        captured["host"] = host
        captured["port"] = port
        return _StubServer()

    import server.app as app

    monkeypatch.setenv("HOST", "0.0.0.0")
    monkeypatch.setenv("PORT", "8123")
    monkeypatch.setattr(app, "make_server", fake_make_server)
    app.main()
    assert captured == {"host": "0.0.0.0", "port": 8123}


def test_discord_requests_carry_real_user_agent():
    """discord.com (Cloudflare) 403s urllib's default UA — every Discord
    request must carry the explicit HTTP_USER_AGENT (live-verified 2026-07-12)."""
    import urllib.request

    from server import auth

    captured = []

    def fake_urlopen(request, timeout=None):
        captured.append(request.get_header("User-agent"))

        class _Resp:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self):
                import json as _json

                return _json.dumps(
                    {"access_token": "tok", "id": "123"}
                ).encode()

        return _Resp()

    real = urllib.request.urlopen
    urllib.request.urlopen = fake_urlopen
    try:
        cfg = auth.AuthConfig("cid", "sec", "https://x/cb", "k" * 32)
        auth.exchange_code(cfg, "code")
        auth.fetch_discord_user("tok")
    finally:
        urllib.request.urlopen = real

    assert captured == [auth.HTTP_USER_AGENT] * 2
    assert "urllib" not in auth.HTTP_USER_AGENT
