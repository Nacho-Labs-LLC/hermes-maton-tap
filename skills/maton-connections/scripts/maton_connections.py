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

BASE_URL = os.environ.get("MATON_BASE_URL", "https://ctrl.maton.ai").rstrip("/")
API_KEY = os.environ.get("MATON_API_KEY", "")


def request(method: str, path: str, body: dict | None = None):
    return request_json(
        f"{BASE_URL}{path}",
        API_KEY,
        method=method,
        body=body,
        urlopen=urllib.request.urlopen,
    )


def main() -> None:
    p = argparse.ArgumentParser(description="Maton connections control-plane helper")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list")
    p_list.add_argument("--app")
    p_list.add_argument("--status")

    p_get = sub.add_parser("get")
    p_get.add_argument("connection_id")

    p_create = sub.add_parser("create")
    p_create.add_argument("app")

    p_delete = sub.add_parser("delete")
    p_delete.add_argument("connection_id")

    args = p.parse_args()
    try:
        if args.cmd == "list":
            qs = {}
            if args.app:
                qs["app"] = args.app
            if args.status:
                qs["status"] = args.status
            suffix = f"?{urllib.parse.urlencode(qs)}" if qs else ""
            status, payload = request("GET", f"/connections{suffix}")
        elif args.cmd == "get":
            status, payload = request(
                "GET", f"/connections/{urllib.parse.quote(args.connection_id)}"
            )
        elif args.cmd == "create":
            status, payload = request("POST", "/connections", {"app": args.app})
        elif args.cmd == "delete":
            status, payload = request(
                "DELETE", f"/connections/{urllib.parse.quote(args.connection_id)}"
            )
        else:
            raise SystemExit("Unknown command")
        print(json.dumps({"status": status, "data": payload}, indent=2))
    except urllib.error.HTTPError as e:
        print_http_error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
