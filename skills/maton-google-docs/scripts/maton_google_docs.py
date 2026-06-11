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
PREFIX = "/google-docs/v1"


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


def document_path(document_id: str, suffix: str = "") -> str:
    return f"/documents/{urllib.parse.quote(document_id, safe='')}{suffix}"


def add_query_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--query",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Extra query parameter. Repeatable.",
    )


def build_location(index: int | None, append: bool) -> dict[str, Any]:
    if append:
        return {"endOfSegmentLocation": {}}
    return {"location": {"index": index if index is not None else 1}}


def build_batch_update_body(args: argparse.Namespace) -> dict[str, Any]:
    payload = load_json_input(args.payload)
    requests = payload.get("requests")
    if not isinstance(requests, list) or not requests:
        raise SystemExit("Batch update payload must include a non-empty requests array")
    return payload


def build_insert_text_body(args: argparse.Namespace) -> dict[str, Any]:
    body = {
        "requests": [
            {
                "insertText": {
                    **build_location(args.index, args.append),
                    "text": args.text,
                }
            }
        ]
    }
    return deep_merge(body, load_json_input(args.payload))


def build_replace_text_body(args: argparse.Namespace) -> dict[str, Any]:
    body = {
        "requests": [
            {
                "replaceAllText": {
                    "containsText": {
                        "text": args.match,
                        "matchCase": args.match_case,
                    },
                    "replaceText": args.replace,
                }
            }
        ]
    }
    return deep_merge(body, load_json_input(args.payload))


def print_response(status: int, payload: dict[str, Any] | list[Any]) -> None:
    print(json.dumps({"status": status, "data": payload}, indent=2))


def main() -> None:
    p = argparse.ArgumentParser(description="Maton Google Docs helper")
    p.add_argument("--connection")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_get = sub.add_parser("get")
    p_get.add_argument("document_id")
    add_query_args(p_get)

    p_create = sub.add_parser("create-document")
    p_create.add_argument("--title", required=True)
    p_create.add_argument(
        "--payload",
        help="Inline JSON object or @path/to/body.json merged into the generated request body.",
    )
    add_query_args(p_create)

    p_batch = sub.add_parser("batch-update")
    p_batch.add_argument("document_id")
    p_batch.add_argument(
        "--payload",
        required=True,
        help="Inline JSON object or @path/to/body.json with a non-empty requests array.",
    )
    add_query_args(p_batch)

    p_insert = sub.add_parser("insert-text")
    p_insert.add_argument("document_id")
    p_insert.add_argument("--text", required=True)
    p_insert.add_argument("--index", type=int)
    p_insert.add_argument("--append", action="store_true")
    p_insert.add_argument(
        "--payload",
        help="Inline JSON object or @path/to/body.json merged into the generated request body.",
    )
    add_query_args(p_insert)

    p_replace = sub.add_parser("replace-text")
    p_replace.add_argument("document_id")
    p_replace.add_argument("--match", required=True)
    p_replace.add_argument("--replace", required=True)
    p_replace.add_argument("--match-case", action=argparse.BooleanOptionalAction, default=True)
    p_replace.add_argument(
        "--payload",
        help="Inline JSON object or @path/to/body.json merged into the generated request body.",
    )
    add_query_args(p_replace)

    args = p.parse_args()

    try:
        if args.cmd == "get":
            status, payload = request(
                "GET",
                document_path(args.document_id),
                connection=args.connection,
                query=parse_queries(args.query),
            )
        elif args.cmd == "create-document":
            body = deep_merge({"title": args.title}, load_json_input(args.payload))
            status, payload = request(
                "POST",
                "/documents",
                connection=args.connection,
                body=body,
                query=parse_queries(args.query),
            )
        elif args.cmd == "batch-update":
            status, payload = request(
                "POST",
                document_path(args.document_id, ":batchUpdate"),
                connection=args.connection,
                body=build_batch_update_body(args),
                query=parse_queries(args.query),
            )
        elif args.cmd == "insert-text":
            status, payload = request(
                "POST",
                document_path(args.document_id, ":batchUpdate"),
                connection=args.connection,
                body=build_insert_text_body(args),
                query=parse_queries(args.query),
            )
        elif args.cmd == "replace-text":
            status, payload = request(
                "POST",
                document_path(args.document_id, ":batchUpdate"),
                connection=args.connection,
                body=build_replace_text_body(args),
                query=parse_queries(args.query),
            )
        else:
            raise SystemExit("Unknown command")
        print_response(status, payload)
    except urllib.error.HTTPError as exc:
        print_http_error(exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
