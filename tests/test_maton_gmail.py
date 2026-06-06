from __future__ import annotations

import json

import pytest
from conftest import run_main


def test_request_requires_api_key(load_module, monkeypatch):
    module = load_module("skills/maton-gmail/scripts/maton_gmail.py", "maton_gmail_missing_key")
    monkeypatch.setattr(module, "API_KEY", "")

    with pytest.raises(SystemExit, match="MATON_API_KEY is not set"):
        module.request("/users/me/profile")


def test_profile_command_passes_connection(load_module, monkeypatch):
    module = load_module("skills/maton-gmail/scripts/maton_gmail.py", "maton_gmail_profile")
    monkeypatch.setattr(module, "API_KEY", "token")

    calls = []

    def fake_request(path, connection=None):
        calls.append((path, connection))
        return 200, {"emailAddress": "user@example.com"}

    monkeypatch.setattr(module, "request", fake_request)

    output = run_main(module, ["--connection", "conn-1", "profile"])
    payload = json.loads(output)

    assert payload["status"] == 200
    assert payload["data"]["emailAddress"] == "user@example.com"
    assert calls == [("/users/me/profile", "conn-1")]


def test_get_command_supports_format_query(load_module, monkeypatch):
    module = load_module("skills/maton-gmail/scripts/maton_gmail.py", "maton_gmail_get")
    monkeypatch.setattr(module, "API_KEY", "token")

    calls = []

    def fake_request(path, connection=None):
        calls.append((path, connection))
        return 200, {"id": "msg-1"}

    monkeypatch.setattr(module, "request", fake_request)

    output = run_main(module, ["get", "msg-1", "--format", "full"])
    payload = json.loads(output)

    assert payload["status"] == 200
    assert payload["data"] == {"id": "msg-1"}
    assert calls == [("/users/me/messages/msg-1?format=full", None)]
