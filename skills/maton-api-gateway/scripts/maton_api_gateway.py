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

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

maton_http = importlib.import_module("maton_http")
build_json_request = maton_http.build_json_request
print_http_error = maton_http.print_http_error
require_api_key = maton_http.require_api_key

BASE_URL = os.environ.get("MATON_GATEWAY_BASE_URL", "https://gateway.maton.ai").rstrip("/")
API_KEY = os.environ.get("MATON_API_KEY", "")


def normalize_path(path: str) -> str:
    return path if path.startswith("/") else f"/{path}"


def parse_query_items(items: list[str] | None) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for item in items or []:
        if "=" not in item:
            raise SystemExit(f"Invalid --query value {item!r}; expected key=value")
        key, value = item.split("=", 1)
        if not key:
            raise SystemExit(f"Invalid --query value {item!r}; key cannot be empty")
        pairs.append((key, value))
    return pairs


def load_body(raw: str | None):
    if raw is None:
        return None
    text = Path(raw[1:]).read_text() if raw.startswith("@") else raw
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        source = raw[1:] if raw.startswith("@") else "inline JSON"
        raise SystemExit(f"Invalid JSON body from {source}: {exc}") from exc


def build_url(app: str, path: str, query_items: list[tuple[str, str]] | None = None) -> str:
    app_prefix = app.strip("/")
    if not app_prefix:
        raise SystemExit("--app is required")
    route = f"/{app_prefix}{normalize_path(path)}"
    suffix = f"?{urllib.parse.urlencode(query_items)}" if query_items else ""
    return f"{BASE_URL}{route}{suffix}"


def request(
    method: str,
    app: str,
    path: str,
    *,
    query_items: list[tuple[str, str]] | None = None,
    body=None,
    connection: str | None = None,
    timeout: int = maton_http.DEFAULT_TIMEOUT,
):
    require_api_key(API_KEY)
    url = build_url(app, path, query_items)
    req = build_json_request(url, API_KEY, method=method, body=body, connection=connection)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = maton_http.decode_json_response(resp)
        return req, resp.status, payload


def add_route_args(parser: argparse.ArgumentParser, *, allow_body: bool) -> None:
    parser.add_argument(
        "--app",
        required=True,
        help="Maton app prefix such as google-mail or google-calendar",
    )
    parser.add_argument(
        "--path",
        required=True,
        help="Route suffix after the app prefix, such as /gmail/v1/users/me/profile",
    )
    parser.add_argument(
        "--query",
        action="append",
        default=[],
        metavar="key=value",
        help="Repeatable query param; use multiple times for multiple params",
    )
    if allow_body:
        parser.add_argument(
            "--body",
            help="Inline JSON or @path/to/body.json",
        )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Generic Maton gateway helper")
    p.add_argument(
        "--connection",
        help="Optional Maton-Connection header for multi-account targeting",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    add_route_args(sub.add_parser("get"), allow_body=False)
    add_route_args(sub.add_parser("post"), allow_body=True)
    add_route_args(sub.add_parser("patch"), allow_body=True)
    add_route_args(sub.add_parser("delete"), allow_body=True)
    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    query_items = parse_query_items(args.query)
    body = load_body(getattr(args, "body", None))
    method = args.cmd.upper()

    try:
        req, status, payload = request(
            method,
            args.app,
            args.path,
            query_items=query_items,
            body=body,
            connection=args.connection,
        )
        print(
            json.dumps(
                {
                    "status": status,
                    "request": {
                        "method": method,
                        "url": req.full_url,
                        "connection": args.connection,
                        "body": body,
                    },
                    "data": payload,
                },
                indent=2,
            )
        )
    except urllib.error.HTTPError as exc:
        print_http_error(exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
