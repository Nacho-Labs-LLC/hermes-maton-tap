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
print_http_error = maton_http.print_http_error
request_json = maton_http.request_json

BASE_URL = os.environ.get("MATON_GATEWAY_BASE_URL", "https://gateway.maton.ai").rstrip("/")
API_KEY = os.environ.get("MATON_API_KEY", "")
PREFIX = "/google-mail/gmail/v1"


def request(path: str, connection: str | None = None):
    return request_json(
        f"{BASE_URL}{PREFIX}{path}",
        API_KEY,
        connection=connection,
        urlopen=urllib.request.urlopen,
    )


def main() -> None:
    p = argparse.ArgumentParser(description="Maton Gmail helper")
    p.add_argument("--connection")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("profile")

    p_list = sub.add_parser("list")
    p_list.add_argument("--query", default=None)
    p_list.add_argument("--max-results", type=int, default=10)

    p_get = sub.add_parser("get")
    p_get.add_argument("message_id")
    p_get.add_argument(
        "--format",
        default=None,
        choices=[None, "metadata", "full", "minimal", "raw"],
    )

    args = p.parse_args()
    try:
        if args.cmd == "profile":
            status, payload = request("/users/me/profile", args.connection)
        elif args.cmd == "list":
            qs = {"maxResults": args.max_results}
            if args.query:
                qs["q"] = args.query
            status, payload = request(
                f"/users/me/messages?{urllib.parse.urlencode(qs)}", args.connection
            )
        elif args.cmd == "get":
            qs = {}
            if args.format:
                qs["format"] = args.format
            suffix = f"?{urllib.parse.urlencode(qs)}" if qs else ""
            status, payload = request(
                f"/users/me/messages/{urllib.parse.quote(args.message_id)}{suffix}",
                args.connection,
            )
        else:
            raise SystemExit("Unknown command")
        print(json.dumps({"status": status, "data": payload}, indent=2))
    except urllib.error.HTTPError as e:
        print_http_error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
