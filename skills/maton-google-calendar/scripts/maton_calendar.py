#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

maton_http = importlib.import_module("maton_http")
print_http_error = maton_http.print_http_error
request_json = maton_http.request_json

BASE_URL = os.environ.get("MATON_GATEWAY_BASE_URL", "https://gateway.maton.ai").rstrip("/")
API_KEY = os.environ.get("MATON_API_KEY", "")
PREFIX = "/google-calendar/calendar/v3"
DEFAULT_CALENDAR_ID = "primary"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_key_value(text: str) -> tuple[str, str]:
    if "=" not in text:
        raise SystemExit(f"Expected key=value, got: {text}")
    key, value = text.split("=", 1)
    if not key:
        raise SystemExit(f"Expected non-empty key in key=value pair: {text}")
    return key, value


def parse_queries(pairs: list[str] | None) -> dict[str, str]:
    query: dict[str, str] = {}
    for pair in pairs or []:
        key, value = parse_key_value(pair)
        query[key] = value
    return query


def load_json_input(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    text = Path(raw[1:]).read_text(encoding="utf-8") if raw.startswith("@") else raw
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise SystemExit("JSON payload must decode to an object")
    return payload


def deep_merge(base: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def build_event_time(date_time: str | None, time_zone: str | None) -> dict[str, str] | None:
    if not date_time:
        return None
    payload = {"dateTime": date_time}
    if time_zone:
        payload["timeZone"] = time_zone
    return payload


def build_attendees(attendees: list[str] | None) -> list[dict[str, str]] | None:
    if not attendees:
        return None
    return [{"email": email} for email in attendees]


def maybe_add_meet(body: dict[str, Any], enabled: bool, request_id: str | None) -> dict[str, Any]:
    if not enabled:
        return body
    meet_request_id = request_id or f"hermes-maton-{uuid.uuid4().hex}"
    return deep_merge(
        body,
        {
            "conferenceData": {
                "createRequest": {
                    "requestId": meet_request_id,
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            }
        },
    )


def request(
    method: str,
    path: str,
    *,
    connection: str | None = None,
    body: dict[str, Any] | None = None,
    query: dict[str, Any] | None = None,
):
    url = f"{BASE_URL}{PREFIX}{path}"
    if query:
        url = f"{url}?{urllib.parse.urlencode(query, doseq=True)}"
    return request_json(
        url,
        API_KEY,
        method=method,
        body=body,
        connection=connection,
        urlopen=urllib.request.urlopen,
    )


def add_calendar_selector(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--calendar-id", default=DEFAULT_CALENDAR_ID)


def add_send_updates(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--send-updates", choices=["all", "externalOnly", "none"])


def add_query_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--query",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Extra query parameter. Repeatable.",
    )


def add_event_patch_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--summary")
    parser.add_argument("--description")
    parser.add_argument("--location")
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--time-zone")
    parser.add_argument("--status")
    parser.add_argument("--attendee", action="append", default=[])
    parser.add_argument(
        "--payload",
        help="Inline JSON object or @path/to/body.json merged into the generated request body.",
    )
    parser.add_argument(
        "--clear-attendees",
        action="store_true",
        help="Set attendees to an empty list.",
    )
    parser.add_argument(
        "--add-meet",
        action="store_true",
        help="Request Google Meet conference data creation.",
    )
    parser.add_argument("--meet-request-id")
    add_send_updates(parser)
    add_query_args(parser)


def event_path(calendar_id: str, event_id: str | None = None) -> str:
    calendar_part = urllib.parse.quote(calendar_id, safe="")
    if event_id is None:
        return f"/calendars/{calendar_part}/events"
    event_part = urllib.parse.quote(event_id, safe="")
    return f"/calendars/{calendar_part}/events/{event_part}"


def build_list_query(args: argparse.Namespace) -> dict[str, Any]:
    query: dict[str, Any] = {
        "maxResults": args.max_results,
        "singleEvents": str(args.single_events).lower(),
        "orderBy": args.order_by,
    }
    if args.time_min:
        query["timeMin"] = args.time_min
    elif not args.include_past:
        query["timeMin"] = utc_now_iso()
    if args.time_max:
        query["timeMax"] = args.time_max
    if args.show_deleted:
        query["showDeleted"] = "true"
    return deep_merge(query, parse_queries(args.query))


def build_create_body(args: argparse.Namespace) -> dict[str, Any]:
    body: dict[str, Any] = {
        "summary": args.summary,
        "start": build_event_time(args.start, args.time_zone),
        "end": build_event_time(args.end, args.time_zone),
    }
    if args.description:
        body["description"] = args.description
    if args.location:
        body["location"] = args.location
    attendees = build_attendees(args.attendee)
    if attendees is not None:
        body["attendees"] = attendees
    body = maybe_add_meet(body, args.add_meet, args.meet_request_id)
    return deep_merge(body, load_json_input(args.payload))


def build_update_body(args: argparse.Namespace) -> dict[str, Any]:
    body: dict[str, Any] = {}
    for field in ("summary", "description", "location", "status"):
        value = getattr(args, field)
        if value is not None:
            body[field] = value
    if args.start:
        body["start"] = build_event_time(args.start, args.time_zone)
    if args.end:
        body["end"] = build_event_time(args.end, args.time_zone)
    if args.clear_attendees:
        body["attendees"] = []
    elif args.attendee:
        body["attendees"] = build_attendees(args.attendee)
    body = maybe_add_meet(body, args.add_meet, args.meet_request_id)
    body = deep_merge(body, load_json_input(args.payload))
    if not body:
        raise SystemExit("No event updates supplied")
    return body


def build_reschedule_body(args: argparse.Namespace) -> dict[str, Any]:
    body = {
        "start": build_event_time(args.start, args.time_zone),
        "end": build_event_time(args.end, args.time_zone),
    }
    return deep_merge(body, load_json_input(args.payload))


def build_attendees_body(args: argparse.Namespace) -> dict[str, Any]:
    attendees = [] if args.clear_attendees else build_attendees(args.attendee)
    if attendees is None:
        raise SystemExit("Provide at least one --attendee or use --clear-attendees")
    return deep_merge({"attendees": attendees}, load_json_input(args.payload))


def main() -> None:
    p = argparse.ArgumentParser(description="Maton Google Calendar helper")
    p.add_argument("--connection")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("calendars")

    def add_list_parser(name: str) -> argparse.ArgumentParser:
        parser = sub.add_parser(name)
        add_calendar_selector(parser)
        parser.add_argument("--max-results", type=int, default=10)
        parser.add_argument("--time-min")
        parser.add_argument("--time-max")
        parser.add_argument("--include-past", action="store_true")
        parser.add_argument("--show-deleted", action="store_true")
        parser.add_argument("--single-events", action=argparse.BooleanOptionalAction, default=True)
        parser.add_argument("--order-by", default="startTime")
        add_query_args(parser)
        return parser

    add_list_parser("upcoming")
    add_list_parser("list-events")

    p_create = sub.add_parser("create-event")
    add_calendar_selector(p_create)
    p_create.add_argument("--summary", required=True)
    p_create.add_argument("--start", required=True)
    p_create.add_argument("--end", required=True)
    p_create.add_argument("--time-zone")
    p_create.add_argument("--description")
    p_create.add_argument("--location")
    p_create.add_argument("--attendee", action="append", default=[])
    p_create.add_argument(
        "--payload",
        help="Inline JSON object or @path/to/body.json merged into the generated request body.",
    )
    p_create.add_argument("--add-meet", action="store_true")
    p_create.add_argument("--meet-request-id")
    add_send_updates(p_create)
    add_query_args(p_create)

    p_update = sub.add_parser("update-event")
    add_calendar_selector(p_update)
    p_update.add_argument("event_id")
    add_event_patch_args(p_update)

    p_reschedule = sub.add_parser("reschedule-event")
    add_calendar_selector(p_reschedule)
    p_reschedule.add_argument("event_id")
    p_reschedule.add_argument("--start", required=True)
    p_reschedule.add_argument("--end", required=True)
    p_reschedule.add_argument("--time-zone")
    p_reschedule.add_argument(
        "--payload",
        help="Inline JSON object or @path/to/body.json merged into the generated request body.",
    )
    add_send_updates(p_reschedule)
    add_query_args(p_reschedule)

    p_attendees = sub.add_parser("update-attendees")
    add_calendar_selector(p_attendees)
    p_attendees.add_argument("event_id")
    p_attendees.add_argument("--attendee", action="append", default=[])
    p_attendees.add_argument(
        "--clear-attendees",
        action="store_true",
        help="Remove every attendee from the event.",
    )
    p_attendees.add_argument(
        "--payload",
        help="Inline JSON object or @path/to/body.json merged into the generated request body.",
    )
    add_send_updates(p_attendees)
    add_query_args(p_attendees)

    p_delete = sub.add_parser("delete-event")
    add_calendar_selector(p_delete)
    p_delete.add_argument("event_id")
    add_send_updates(p_delete)
    add_query_args(p_delete)

    args = p.parse_args()
    try:
        if args.cmd == "calendars":
            status, payload = request("GET", "/users/me/calendarList", connection=args.connection)
        elif args.cmd in {"upcoming", "list-events"}:
            status, payload = request(
                "GET",
                event_path(args.calendar_id),
                connection=args.connection,
                query=build_list_query(args),
            )
        elif args.cmd == "create-event":
            query = parse_queries(args.query)
            if args.send_updates:
                query["sendUpdates"] = args.send_updates
            if args.add_meet and "conferenceDataVersion" not in query:
                query["conferenceDataVersion"] = "1"
            status, payload = request(
                "POST",
                event_path(args.calendar_id),
                connection=args.connection,
                body=build_create_body(args),
                query=query,
            )
        elif args.cmd == "update-event":
            query = parse_queries(args.query)
            if args.send_updates:
                query["sendUpdates"] = args.send_updates
            if args.add_meet and "conferenceDataVersion" not in query:
                query["conferenceDataVersion"] = "1"
            status, payload = request(
                "PATCH",
                event_path(args.calendar_id, args.event_id),
                connection=args.connection,
                body=build_update_body(args),
                query=query,
            )
        elif args.cmd == "reschedule-event":
            query = parse_queries(args.query)
            if args.send_updates:
                query["sendUpdates"] = args.send_updates
            status, payload = request(
                "PATCH",
                event_path(args.calendar_id, args.event_id),
                connection=args.connection,
                body=build_reschedule_body(args),
                query=query,
            )
        elif args.cmd == "update-attendees":
            query = parse_queries(args.query)
            if args.send_updates:
                query["sendUpdates"] = args.send_updates
            status, payload = request(
                "PATCH",
                event_path(args.calendar_id, args.event_id),
                connection=args.connection,
                body=build_attendees_body(args),
                query=query,
            )
        elif args.cmd == "delete-event":
            query = parse_queries(args.query)
            if args.send_updates:
                query["sendUpdates"] = args.send_updates
            status, payload = request(
                "DELETE",
                event_path(args.calendar_id, args.event_id),
                connection=args.connection,
                query=query,
            )
        else:
            raise SystemExit("Unknown command")
        print(json.dumps({"status": status, "data": payload}, indent=2))
    except urllib.error.HTTPError as e:
        print_http_error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
