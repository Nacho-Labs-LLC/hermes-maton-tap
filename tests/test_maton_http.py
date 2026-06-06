from __future__ import annotations

import json

from conftest import FakeJsonResponse, make_http_error, run_main_expect_exit


def test_gmail_request_adds_connection_header(load_module, monkeypatch):
    module = load_module("skills/maton-gmail/scripts/maton_gmail.py", "maton_gmail_request")
    monkeypatch.setattr(module, "API_KEY", "token")
    monkeypatch.setattr(module, "BASE_URL", "https://gateway.example")

    seen = {}

    def fake_urlopen(request, timeout=60):
        seen["url"] = request.full_url
        seen["timeout"] = timeout
        seen["headers"] = dict(request.header_items())
        return FakeJsonResponse({"messages": []}, status=200)

    monkeypatch.setattr(module.urllib.request, "urlopen", fake_urlopen)

    status, payload = module.request("/users/me/messages", connection="conn-123")

    assert status == 200
    assert payload == {"messages": []}
    assert seen["url"] == "https://gateway.example/google-mail/gmail/v1/users/me/messages"
    assert seen["headers"]["Maton-connection"] == "conn-123"
    assert seen["headers"]["Authorization"] == "Bearer token"


def test_calendar_main_emits_structured_http_error(load_module, monkeypatch):
    module = load_module(
        "skills/maton-google-calendar/scripts/maton_calendar.py",
        "maton_calendar_http_error",
    )

    def fake_request(method, path, *, connection=None, body=None, query=None):
        raise make_http_error(403, {"message": "forbidden"})

    monkeypatch.setattr(module, "request", fake_request)

    code, output = run_main_expect_exit(module, ["calendars"])

    assert code == 1
    assert json.loads(output) == {"status": 403, "error": {"message": "forbidden"}}
