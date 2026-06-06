from __future__ import annotations

import json

import pytest
from conftest import FakeJsonResponse, make_http_error, run_main, run_main_expect_exit


def test_request_builds_app_prefixed_url_and_connection_header(load_module, monkeypatch):
    module = load_module(
        "skills/maton-api-gateway/scripts/maton_api_gateway.py",
        "maton_api_gateway_request",
    )
    monkeypatch.setattr(module, "API_KEY", "token")
    monkeypatch.setattr(module, "BASE_URL", "https://gateway.example")

    seen = {}

    def fake_urlopen(request, timeout=60):
        seen["url"] = request.full_url
        seen["timeout"] = timeout
        seen["headers"] = dict(request.header_items())
        return FakeJsonResponse({"ok": True}, status=200)

    monkeypatch.setattr(module.urllib.request, "urlopen", fake_urlopen)

    req, status, payload = module.request(
        "GET",
        "google-mail",
        "/gmail/v1/users/me/messages",
        query_items=[("maxResults", "5"), ("q", "is:unread in:inbox")],
        connection="conn-123",
    )

    assert status == 200
    assert payload == {"ok": True}
    assert req.full_url == seen["url"]
    assert seen["url"] == "https://gateway.example/google-mail/gmail/v1/users/me/messages?maxResults=5&q=is%3Aunread+in%3Ainbox"
    assert seen["headers"]["Maton-connection"] == "conn-123"
    assert seen["headers"]["Authorization"] == "Bearer token"


def test_post_command_supports_inline_json_body(load_module, monkeypatch):
    module = load_module(
        "skills/maton-api-gateway/scripts/maton_api_gateway.py",
        "maton_api_gateway_post",
    )
    monkeypatch.setattr(module, "API_KEY", "token")

    calls = []

    def fake_request(
        method,
        app,
        path,
        *,
        query_items=None,
        body=None,
        connection=None,
        timeout=60,
    ):
        calls.append((method, app, path, query_items, body, connection, timeout))
        request_obj = type(
            "Req",
            (),
            {
                "full_url": (
                    "https://gateway.example/google-calendar/"
                    "calendar/v3/calendars/primary/events"
                )
            },
        )()
        return request_obj, 201, {"id": "evt-1"}

    monkeypatch.setattr(module, "request", fake_request)

    output = run_main(
        module,
        [
            "--connection",
            "conn-1",
            "post",
            "--app",
            "google-calendar",
            "--path",
            "/calendar/v3/calendars/primary/events",
            "--body",
            '{"summary":"Demo"}',
        ],
    )
    payload = json.loads(output)

    assert payload["status"] == 201
    assert payload["request"]["method"] == "POST"
    assert payload["request"]["connection"] == "conn-1"
    assert payload["request"]["body"] == {"summary": "Demo"}
    assert payload["data"] == {"id": "evt-1"}
    assert calls == [
        (
            "POST",
            "google-calendar",
            "/calendar/v3/calendars/primary/events",
            [],
            {"summary": "Demo"},
            "conn-1",
            60,
        )
    ]


def test_load_body_supports_json_file(load_module, tmp_path):
    module = load_module(
        "skills/maton-api-gateway/scripts/maton_api_gateway.py",
        "maton_api_gateway_body_file",
    )
    body_path = tmp_path / "payload.json"
    body_path.write_text('{"hello":"world"}')

    assert module.load_body(f"@{body_path}") == {"hello": "world"}


def test_invalid_query_value_exits(load_module):
    module = load_module(
        "skills/maton-api-gateway/scripts/maton_api_gateway.py",
        "maton_api_gateway_bad_query",
    )

    with pytest.raises(SystemExit, match="expected key=value"):
        module.parse_query_items(["bad-query"])


def test_http_error_returns_structured_json(load_module, monkeypatch):
    module = load_module(
        "skills/maton-api-gateway/scripts/maton_api_gateway.py",
        "maton_api_gateway_http_error",
    )

    def fake_request(
        method,
        app,
        path,
        *,
        query_items=None,
        body=None,
        connection=None,
        timeout=60,
    ):
        raise make_http_error(404, {"message": "missing"})

    monkeypatch.setattr(module, "request", fake_request)

    code, output = run_main_expect_exit(
        module,
        ["get", "--app", "google-mail", "--path", "/gmail/v1/users/me/profile"],
    )

    assert code == 1
    assert json.loads(output) == {"status": 404, "error": {"message": "missing"}}
