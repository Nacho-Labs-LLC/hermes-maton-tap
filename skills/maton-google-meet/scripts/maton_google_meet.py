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
PREFIX = "/google-meet/v2"


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


def normalize_resource_id(value: str, prefix: str) -> str:
    trimmed = value.strip()
    if trimmed.startswith(f"{prefix}/"):
        return trimmed[len(prefix) + 1 :]
    return trimmed


def conference_record_path(record_id: str, suffix: str = "") -> str:
    record_part = urllib.parse.quote(normalize_resource_id(record_id, "conferenceRecords"), safe="")
    return f"/conferenceRecords/{record_part}{suffix}"


def space_path(space: str) -> str:
    space_part = urllib.parse.quote(normalize_resource_id(space, "spaces"), safe="")
    return f"/spaces/{space_part}"


def add_query_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--query",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Extra query parameter. Repeatable.",
    )


def main() -> None:
    p = argparse.ArgumentParser(description="Maton Google Meet helper")
    p.add_argument("--connection")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list-records")
    p_list.add_argument("--page-size", type=int)
    add_query_args(p_list)

    p_get = sub.add_parser("get-record")
    p_get.add_argument("record_id")

    p_participants = sub.add_parser("participants")
    p_participants.add_argument("record_id")
    p_participants.add_argument("--page-size", type=int)
    add_query_args(p_participants)

    p_create_space = sub.add_parser("create-space")
    p_create_space.add_argument(
        "--payload",
        help="Inline JSON object or @path/to/body.json sent to POST /v2/spaces. Defaults to {}.",
    )

    p_get_space = sub.add_parser("get-space")
    p_get_space.add_argument("space")

    args = p.parse_args()
    try:
        if args.cmd == "list-records":
            query = parse_queries(args.query)
            if args.page_size is not None:
                query["pageSize"] = str(args.page_size)
            status, payload = request(
                "GET",
                "/conferenceRecords",
                connection=args.connection,
                query=query,
            )
        elif args.cmd == "get-record":
            status, payload = request(
                "GET",
                conference_record_path(args.record_id),
                connection=args.connection,
            )
        elif args.cmd == "participants":
            query = parse_queries(args.query)
            if args.page_size is not None:
                query["pageSize"] = str(args.page_size)
            status, payload = request(
                "GET",
                conference_record_path(args.record_id, "/participants"),
                connection=args.connection,
                query=query,
            )
        elif args.cmd == "create-space":
            status, payload = request(
                "POST",
                "/spaces",
                connection=args.connection,
                body=load_json_input(args.payload),
            )
        elif args.cmd == "get-space":
            status, payload = request(
                "GET",
                space_path(args.space),
                connection=args.connection,
            )
        else:
            raise SystemExit("Unknown command")
        print(json.dumps({"status": status, "data": payload}, indent=2))
    except urllib.error.HTTPError as e:
        print_http_error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
