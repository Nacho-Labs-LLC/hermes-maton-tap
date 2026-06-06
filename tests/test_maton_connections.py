from __future__ import annotations

import json

import pytest
from conftest import make_http_error, run_main, run_main_expect_exit


def test_request_requires_api_key(load_module, monkeypatch):
    module = load_module(
        "skills/maton-connections/scripts/maton_connections.py",
        "maton_connections_missing_key",
    )
    monkeypatch.setattr(module, "API_KEY", "")

    with pytest.raises(SystemExit, match="MATON_API_KEY is not set"):
        module.request("GET", "/connections")


def test_list_command_builds_query_and_prints_json(load_module, monkeypatch):
    module = load_module(
        "skills/maton-connections/scripts/maton_connections.py",
        "maton_connections_cli",
    )
    monkeypatch.setattr(module, "API_KEY", "token")

    calls = []

    def fake_request(method, path, body=None):
        calls.append((method, path, body))
        return 200, {"items": []}

    monkeypatch.setattr(module, "request", fake_request)

    output = run_main(module, ["list", "--app", "gmail", "--status", "active"])
    payload = json.loads(output)

    assert payload["status"] == 200
    assert payload["data"] == {"items": []}
    assert calls == [("GET", "/connections?app=gmail&status=active", None)]


def test_http_error_returns_structured_json(load_module, monkeypatch):
    module = load_module(
        "skills/maton-connections/scripts/maton_connections.py",
        "maton_connections_http_error",
    )

    def fake_request(method, path, body=None):
        raise make_http_error(404, {"message": "missing"})

    monkeypatch.setattr(module, "request", fake_request)

    code, output = run_main_expect_exit(module, ["get", "abc123"])

    assert code == 1
    payload = json.loads(output)
    assert payload == {"status": 404, "error": {"message": "missing"}}
