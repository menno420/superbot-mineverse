"""API tests for the stage-1 backend (stdlib server, real HTTP round-trips)."""

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from server.app import SNAPSHOT_PATH, WEB_ROOT  # noqa: E402

# The kwargs-taking ``serve`` fixture lives in tests/conftest.py
# (wrapping tests/_server_helpers.serve_factory).


def fetch(url):
    with urllib.request.urlopen(url) as res:
        return res.status, res.headers, res.read()


def test_snapshot_route_status_and_content_type(serve):
    status, headers, body = fetch(serve() + "/api/snapshot")
    assert status == 200
    assert headers["Content-Type"].startswith("application/json")
    assert body == SNAPSHOT_PATH.read_bytes()


def test_snapshot_route_payload_shape(serve):
    _, _, body = fetch(serve() + "/api/snapshot")
    payload = json.loads(body)
    # READ contract v1 envelope (docs/mining-data-contract.md).
    assert payload["schema_version"] == "1"
    assert payload["generated_at"]
    assert isinstance(payload["guild_id"], str)
    assert payload["miners"], "snapshot must ship miners"
    for miner in payload["miners"]:
        assert "mining_inventory" in miner
        assert "depth" in miner
        assert "xp" in miner
        assert "equipment" in miner
        assert "vault" in miner


def test_frontend_is_served(serve):
    base = serve()
    status, headers, body = fetch(base + "/")
    assert status == 200
    assert headers["Content-Type"].startswith("text/html")
    assert b"app.js" in body
    status, headers, _ = fetch(base + "/app.js")
    assert status == 200


def test_unknown_api_route_is_404(serve):
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        fetch(serve() + "/api/nope")
    assert excinfo.value.code == 404


def test_missing_snapshot_is_honest_503(serve, tmp_path):
    base = serve(snapshot_path=tmp_path / "gone.json", web_root=WEB_ROOT)
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        fetch(base + "/api/snapshot")
    assert excinfo.value.code == 503
    assert json.loads(excinfo.value.read())["error"] == "snapshot unavailable"


def test_corrupt_snapshot_is_honest_503(serve, tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    base = serve(snapshot_path=bad, web_root=WEB_ROOT)
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        fetch(base + "/api/snapshot")
    assert excinfo.value.code == 503
