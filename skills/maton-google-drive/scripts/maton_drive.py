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
PREFIX = "/google-drive/drive/v3"
DEFAULT_ABOUT_FIELDS = "user,storageQuota,importFormats,exportFormats,maxUploadSize"
DEFAULT_LIST_FIELDS = (
    "nextPageToken,files(id,name,mimeType,modifiedTime,webViewLink,parents,driveId,shared,trashed)"
)
DEFAULT_FILE_FIELDS = (
    "id,name,mimeType,size,createdTime,modifiedTime,parents,owners(displayName,emailAddress),"
    "webViewLink,iconLink,driveId,shared,trashed,starred"
)


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


def request(path: str, connection: str | None = None, query: dict[str, Any] | None = None):
    url = f"{BASE_URL}{PREFIX}{path}"
    if query:
        url = f"{url}?{urllib.parse.urlencode(query, doseq=True)}"
    return request_json(
        url,
        API_KEY,
        connection=connection,
        urlopen=urllib.request.urlopen,
    )


def build_drive_q(args: argparse.Namespace) -> str | None:
    clauses: list[str] = []
    if args.search:
        clauses.append(args.search)
    if args.folder_id:
        clauses.append(f"'{args.folder_id}' in parents")
    if args.shared_with_me:
        clauses.append("sharedWithMe = true")
    if not args.include_trashed:
        clauses.append("trashed = false")
    return " and ".join(clauses) if clauses else None


def build_list_query(args: argparse.Namespace) -> dict[str, Any]:
    query: dict[str, Any] = {
        "pageSize": args.page_size,
        "fields": args.fields,
    }
    if args.page_token:
        query["pageToken"] = args.page_token
    if args.order_by:
        query["orderBy"] = args.order_by
    if args.spaces:
        query["spaces"] = args.spaces
    if args.corpora:
        query["corpora"] = args.corpora
    if args.drive_id:
        query["driveId"] = args.drive_id

    supports_all_drives = args.supports_all_drives
    include_items = args.include_items_from_all_drives
    if args.drive_id:
        if supports_all_drives is None:
            supports_all_drives = True
        if include_items is None:
            include_items = True
    if supports_all_drives is not None:
        query["supportsAllDrives"] = str(supports_all_drives).lower()
    if include_items is not None:
        query["includeItemsFromAllDrives"] = str(include_items).lower()

    drive_q = build_drive_q(args)
    if drive_q:
        query["q"] = drive_q
    return {**query, **parse_queries(args.query)}


def add_query_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--query",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Extra query parameter. Repeatable.",
    )


def add_drive_scope_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--spaces", help="Drive spaces to search, e.g. drive or appDataFolder")
    parser.add_argument("--corpora", choices=["user", "domain", "drive", "allDrives"])
    parser.add_argument("--drive-id")
    parser.add_argument(
        "--supports-all-drives",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Set supportsAllDrives=true/false. Auto-enabled when --drive-id "
            "is set unless overridden."
        ),
    )
    parser.add_argument(
        "--include-items-from-all-drives",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Set includeItemsFromAllDrives=true/false. Auto-enabled when "
            "--drive-id is set unless overridden."
        ),
    )


def add_list_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--search", help="Drive q expression, e.g. name contains 'roadmap'")
    parser.add_argument("--folder-id", help="Restrict results to direct children of this folder")
    parser.add_argument(
        "--shared-with-me",
        action="store_true",
        help="Add sharedWithMe = true to the Drive q expression",
    )
    parser.add_argument(
        "--include-trashed",
        action="store_true",
        help="Do not auto-append trashed = false",
    )
    parser.add_argument("--page-size", type=int, default=25)
    parser.add_argument("--page-token")
    parser.add_argument("--order-by")
    parser.add_argument("--fields", default=DEFAULT_LIST_FIELDS)
    add_drive_scope_args(parser)
    add_query_args(parser)


def main() -> None:
    p = argparse.ArgumentParser(description="Maton Google Drive helper")
    p.add_argument("--connection")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_about = sub.add_parser("about")
    p_about.add_argument("--fields", default=DEFAULT_ABOUT_FIELDS)
    add_query_args(p_about)

    p_list = sub.add_parser("list-files")
    add_list_args(p_list)

    p_shared = sub.add_parser("shared-with-me")
    add_list_args(p_shared)

    p_get = sub.add_parser("get-file")
    p_get.add_argument("file_id")
    p_get.add_argument("--fields", default=DEFAULT_FILE_FIELDS)
    add_drive_scope_args(p_get)
    add_query_args(p_get)

    args = p.parse_args()
    try:
        if args.cmd == "about":
            query = {"fields": args.fields, **parse_queries(args.query)}
            status, payload = request("/about", args.connection, query)
        elif args.cmd in {"list-files", "shared-with-me"}:
            if args.cmd == "shared-with-me":
                args.shared_with_me = True
            status, payload = request("/files", args.connection, build_list_query(args))
        elif args.cmd == "get-file":
            query = {"fields": args.fields}
            if args.supports_all_drives is not None:
                query["supportsAllDrives"] = str(args.supports_all_drives).lower()
            if args.include_items_from_all_drives is not None:
                query["includeItemsFromAllDrives"] = str(args.include_items_from_all_drives).lower()
            if args.drive_id:
                query["driveId"] = args.drive_id
            if args.corpora:
                query["corpora"] = args.corpora
            if args.spaces:
                query["spaces"] = args.spaces
            query.update(parse_queries(args.query))
            status, payload = request(
                f"/files/{urllib.parse.quote(args.file_id, safe='')}",
                args.connection,
                query,
            )
        else:
            raise SystemExit("Unknown command")
        print(json.dumps({"status": status, "data": payload}, indent=2))
    except urllib.error.HTTPError as e:
        print_http_error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
