from __future__ import annotations

import json

import pytest
from conftest import make_http_error, run_main, run_main_expect_exit


@pytest.fixture
def module(load_module):
    return load_module(
        "skills/maton-google-meet/scripts/maton_google_meet.py",
        "maton_google_meet_under_test",
    )


def test_request_requires_api_key(module, monkeypatch):
    monkeypatch.setattr(module, "API_KEY", "")

    with pytest.raises(SystemExit, match="MATON_API_KEY is not set"):
        module.request("GET", "/conferenceRecords")


def test_list_records_builds_query_and_connection(module, monkeypatch):
    monkeypatch.setattr(module, "API_KEY", "token")

    calls = []

    def fake_request(method, path, **kwargs):
        calls.append((method, path, kwargs))
        return 200, {"conferenceRecords": []}

    monkeypatch.setattr(module, "request", fake_request)

    output = run_main(
        module,
        [
            "--connection",
            "conn-7",
            "list-records",
            "--page-size",
            "5",
            "--query",
            "filter=space.meeting_code=abc-defg-hij",
        ],
    )
    payload = json.loads(output)

    assert payload == {"status": 200, "data": {"conferenceRecords": []}}
    assert calls == [
        (
            "GET",
            "/conferenceRecords",
            {
                "connection": "conn-7",
                "query": {
                    "filter": "space.meeting_code=abc-defg-hij",
                    "pageSize": "5",
                },
            },
        )
    ]


def test_get_record_normalizes_full_resource_name(module, monkeypatch):
    monkeypatch.setattr(module, "API_KEY", "token")

    calls = []

    def fake_request(method, path, **kwargs):
        calls.append((method, path, kwargs))
        return 200, {"name": "conferenceRecords/abc123"}

    monkeypatch.setattr(module, "request", fake_request)

    output = run_main(module, ["get-record", "conferenceRecords/abc123"])
    payload = json.loads(output)

    assert payload["status"] == 200
    assert payload["data"] == {"name": "conferenceRecords/abc123"}
    assert calls == [
        (
            "GET",
            "/conferenceRecords/abc123",
            {"connection": None},
        )
    ]


def test_participants_builds_nested_path(module, monkeypatch):
    monkeypatch.setattr(module, "API_KEY", "token")

    calls = []

    def fake_request(method, path, **kwargs):
        calls.append((method, path, kwargs))
        return 200, {"participants": []}

    monkeypatch.setattr(module, "request", fake_request)

    run_main(
        module,
        [
            "participants",
            "abc123",
            "--page-size",
            "20",
            "--query",
            "pageToken=next-page",
        ],
    )

    assert calls == [
        (
            "GET",
            "/conferenceRecords/abc123/participants",
            {
                "connection": None,
                "query": {
                    "pageToken": "next-page",
                    "pageSize": "20",
                },
            },
        )
    ]


def test_create_space_supports_inline_payload(module, monkeypatch):
    monkeypatch.setattr(module, "API_KEY", "token")

    calls = []

    def fake_request(method, path, **kwargs):
        calls.append((method, path, kwargs))
        return 201, {"name": "spaces/xyz789"}

    monkeypatch.setattr(module, "request", fake_request)

    output = run_main(
        module,
        [
            "--connection",
            "conn-9",
            "create-space",
            "--payload",
            '{"config":{"accessType":"OPEN"}}',
        ],
    )
    payload = json.loads(output)

    assert payload == {"status": 201, "data": {"name": "spaces/xyz789"}}
    assert calls == [
        (
            "POST",
            "/spaces",
            {
                "connection": "conn-9",
                "body": {"config": {"accessType": "OPEN"}},
            },
        )
    ]


def test_get_space_normalizes_full_resource_name(module, monkeypatch):
    monkeypatch.setattr(module, "API_KEY", "token")

    calls = []

    def fake_request(method, path, **kwargs):
        calls.append((method, path, kwargs))
        return 200, {"name": "spaces/xyz789"}

    monkeypatch.setattr(module, "request", fake_request)

    run_main(module, ["get-space", "spaces/xyz789"])

    assert calls == [
        (
            "GET",
            "/spaces/xyz789",
            {"connection": None},
        )
    ]


def test_http_error_returns_structured_json(module, monkeypatch):
    def fake_request(method, path, **kwargs):
        raise make_http_error(404, {"message": "missing"})

    monkeypatch.setattr(module, "request", fake_request)

    code, output = run_main_expect_exit(module, ["get-record", "abc123"])

    assert code == 1
    assert json.loads(output) == {"status": 404, "error": {"message": "missing"}}
