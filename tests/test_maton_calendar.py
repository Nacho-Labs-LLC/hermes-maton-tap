from __future__ import annotations

import json

import pytest
from conftest import run_main


@pytest.fixture
def module(load_module):
    return load_module(
        "skills/maton-google-calendar/scripts/maton_calendar.py",
        "maton_calendar_under_test",
    )


def test_request_requires_api_key(module, monkeypatch):
    monkeypatch.setattr(module, "API_KEY", "")

    with pytest.raises(SystemExit, match="MATON_API_KEY is not set"):
        module.request("GET", "/users/me/calendarList")


def test_upcoming_command_builds_expected_query(module, monkeypatch):
    monkeypatch.setattr(module, "API_KEY", "token")

    calls = []

    def fake_request(method, path, **kwargs):
        calls.append((method, path, kwargs))
        return 200, {"items": []}

    monkeypatch.setattr(module, "request", fake_request)

    output = run_main(
        module,
        [
            "--connection",
            "conn-9",
            "upcoming",
            "--calendar-id",
            "team/calendar",
            "--max-results",
            "5",
            "--time-min",
            "2026-06-05T00:00:00Z",
            "--time-max",
            "2026-06-06T00:00:00Z",
        ],
    )
    payload = json.loads(output)

    assert payload["status"] == 200
    assert payload["data"] == {"items": []}
    assert calls == [
        (
            "GET",
            "/calendars/team%2Fcalendar/events",
            {
                "connection": "conn-9",
                "query": {
                    "maxResults": 5,
                    "singleEvents": "true",
                    "orderBy": "startTime",
                    "timeMin": "2026-06-05T00:00:00Z",
                    "timeMax": "2026-06-06T00:00:00Z",
                },
            },
        )
    ]


def test_upcoming_defaults_time_min_to_now(module, monkeypatch):
    monkeypatch.setattr(module, "API_KEY", "token")
    monkeypatch.setattr(module, "utc_now_iso", lambda: "2026-06-05T12:34:56Z")

    calls = []

    def fake_request(method, path, **kwargs):
        calls.append((method, path, kwargs))
        return 200, {"items": []}

    monkeypatch.setattr(module, "request", fake_request)

    run_main(module, ["upcoming"])

    assert calls == [
        (
            "GET",
            "/calendars/primary/events",
            {
                "connection": None,
                "query": {
                    "maxResults": 10,
                    "singleEvents": "true",
                    "orderBy": "startTime",
                    "timeMin": "2026-06-05T12:34:56Z",
                },
            },
        )
    ]


def test_list_events_include_past_skips_default_time_min(module, monkeypatch):
    monkeypatch.setattr(module, "API_KEY", "token")

    calls = []

    def fake_request(method, path, **kwargs):
        calls.append((method, path, kwargs))
        return 200, {"items": []}

    monkeypatch.setattr(module, "request", fake_request)

    run_main(module, ["list-events", "--include-past", "--query", "q=custom"])

    assert calls == [
        (
            "GET",
            "/calendars/primary/events",
            {
                "connection": None,
                "query": {
                    "maxResults": 10,
                    "singleEvents": "true",
                    "orderBy": "startTime",
                    "q": "custom",
                },
            },
        )
    ]


def test_create_event_builds_body_and_meet_query(module, monkeypatch, tmp_path):
    monkeypatch.setattr(module, "API_KEY", "token")
    payload_path = tmp_path / "create_payload.json"
    payload_path.write_text('{"guestsCanModify": true}', encoding="utf-8")

    calls = []

    def fake_request(method, path, **kwargs):
        calls.append((method, path, kwargs))
        return 200, {"id": "evt-1"}

    monkeypatch.setattr(module, "request", fake_request)

    output = run_main(
        module,
        [
            "--connection",
            "conn-1",
            "create-event",
            "--calendar-id",
            "team/calendar",
            "--summary",
            "Standup",
            "--start",
            "2026-06-05T13:00:00Z",
            "--end",
            "2026-06-05T13:30:00Z",
            "--time-zone",
            "UTC",
            "--description",
            "Daily sync",
            "--location",
            "Zoom",
            "--attendee",
            "a@example.com",
            "--attendee",
            "b@example.com",
            "--add-meet",
            "--meet-request-id",
            "meet-123",
            "--send-updates",
            "all",
            "--query",
            "supportsAttachments=true",
            "--payload",
            f"@{payload_path}",
        ],
    )
    parsed = json.loads(output)

    assert parsed == {"status": 200, "data": {"id": "evt-1"}}
    assert calls == [
        (
            "POST",
            "/calendars/team%2Fcalendar/events",
            {
                "connection": "conn-1",
                "body": {
                    "summary": "Standup",
                    "start": {"dateTime": "2026-06-05T13:00:00Z", "timeZone": "UTC"},
                    "end": {"dateTime": "2026-06-05T13:30:00Z", "timeZone": "UTC"},
                    "description": "Daily sync",
                    "location": "Zoom",
                    "attendees": [
                        {"email": "a@example.com"},
                        {"email": "b@example.com"},
                    ],
                    "conferenceData": {
                        "createRequest": {
                            "requestId": "meet-123",
                            "conferenceSolutionKey": {"type": "hangoutsMeet"},
                        }
                    },
                    "guestsCanModify": True,
                },
                "query": {
                    "supportsAttachments": "true",
                    "sendUpdates": "all",
                    "conferenceDataVersion": "1",
                },
            },
        )
    ]


def test_update_event_builds_partial_patch(module, monkeypatch):
    monkeypatch.setattr(module, "API_KEY", "token")

    class FakeUuid:
        hex = "deadbeef"

    calls = []

    def fake_request(method, path, **kwargs):
        calls.append((method, path, kwargs))
        return 200, {"id": "evt-2"}

    monkeypatch.setattr(module.uuid, "uuid4", lambda: FakeUuid())
    monkeypatch.setattr(module, "request", fake_request)

    run_main(
        module,
        [
            "update-event",
            "evt-2",
            "--summary",
            "Updated title",
            "--start",
            "2026-06-05T15:00:00Z",
            "--time-zone",
            "America/New_York",
            "--attendee",
            "new@example.com",
            "--payload",
            '{"extendedProperties": {"private": {"source": "hermes"}}}',
            "--send-updates",
            "externalOnly",
            "--add-meet",
        ],
    )

    assert calls == [
        (
            "PATCH",
            "/calendars/primary/events/evt-2",
            {
                "connection": None,
                "body": {
                    "summary": "Updated title",
                    "start": {
                        "dateTime": "2026-06-05T15:00:00Z",
                        "timeZone": "America/New_York",
                    },
                    "attendees": [{"email": "new@example.com"}],
                    "conferenceData": {
                        "createRequest": {
                            "requestId": "hermes-maton-deadbeef",
                            "conferenceSolutionKey": {"type": "hangoutsMeet"},
                        }
                    },
                    "extendedProperties": {"private": {"source": "hermes"}},
                },
                "query": {
                    "sendUpdates": "externalOnly",
                    "conferenceDataVersion": "1",
                },
            },
        )
    ]


def test_update_event_requires_changes(module, monkeypatch):
    monkeypatch.setattr(module, "API_KEY", "token")
    monkeypatch.setattr(module, "request", lambda *args, **kwargs: (200, {}))

    with pytest.raises(SystemExit, match="No event updates supplied"):
        run_main(module, ["update-event", "evt-2"])


def test_reschedule_event_builds_time_patch(module, monkeypatch):
    monkeypatch.setattr(module, "API_KEY", "token")

    calls = []

    def fake_request(method, path, **kwargs):
        calls.append((method, path, kwargs))
        return 200, {"id": "evt-3"}

    monkeypatch.setattr(module, "request", fake_request)

    run_main(
        module,
        [
            "reschedule-event",
            "evt-3",
            "--start",
            "2026-06-05T16:00:00Z",
            "--end",
            "2026-06-05T17:00:00Z",
            "--time-zone",
            "UTC",
            "--send-updates",
            "none",
        ],
    )

    assert calls == [
        (
            "PATCH",
            "/calendars/primary/events/evt-3",
            {
                "connection": None,
                "body": {
                    "start": {"dateTime": "2026-06-05T16:00:00Z", "timeZone": "UTC"},
                    "end": {"dateTime": "2026-06-05T17:00:00Z", "timeZone": "UTC"},
                },
                "query": {"sendUpdates": "none"},
            },
        )
    ]


def test_update_attendees_supports_clear(module, monkeypatch):
    monkeypatch.setattr(module, "API_KEY", "token")

    calls = []

    def fake_request(method, path, **kwargs):
        calls.append((method, path, kwargs))
        return 200, {"id": "evt-4"}

    monkeypatch.setattr(module, "request", fake_request)

    run_main(module, ["update-attendees", "evt-4", "--clear-attendees"])

    assert calls == [
        (
            "PATCH",
            "/calendars/primary/events/evt-4",
            {
                "connection": None,
                "body": {"attendees": []},
                "query": {},
            },
        )
    ]


def test_delete_event_builds_delete_request(module, monkeypatch):
    monkeypatch.setattr(module, "API_KEY", "token")

    calls = []

    def fake_request(method, path, **kwargs):
        calls.append((method, path, kwargs))
        return 204, {}

    monkeypatch.setattr(module, "request", fake_request)

    run_main(
        module,
        [
            "delete-event",
            "evt-5",
            "--calendar-id",
            "team/calendar",
            "--send-updates",
            "all",
            "--query",
            "foo=bar",
        ],
    )

    assert calls == [
        (
            "DELETE",
            "/calendars/team%2Fcalendar/events/evt-5",
            {
                "connection": None,
                "query": {"foo": "bar", "sendUpdates": "all"},
            },
        )
    ]
