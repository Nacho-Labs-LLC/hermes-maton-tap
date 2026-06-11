from __future__ import annotations

import json

import pytest
from conftest import run_main


@pytest.fixture
def module(load_module):
    return load_module(
        "skills/maton-google-drive/scripts/maton_drive.py",
        "maton_drive_under_test",
    )


def test_request_requires_api_key(module, monkeypatch):
    monkeypatch.setattr(module, "API_KEY", "")

    with pytest.raises(SystemExit, match="MATON_API_KEY is not set"):
        module.request("/about")


def test_about_command_builds_default_fields_query(module, monkeypatch):
    monkeypatch.setattr(module, "API_KEY", "token")

    calls = []

    def fake_request(path, connection=None, query=None):
        calls.append((path, connection, query))
        return 200, {"user": {"displayName": "Drive User"}}

    monkeypatch.setattr(module, "request", fake_request)

    output = run_main(module, ["--connection", "conn-1", "about"])
    payload = json.loads(output)

    assert payload == {"status": 200, "data": {"user": {"displayName": "Drive User"}}}
    assert calls == [
        (
            "/about",
            "conn-1",
            {"fields": module.DEFAULT_ABOUT_FIELDS},
        )
    ]


def test_list_files_builds_expected_query(module, monkeypatch):
    monkeypatch.setattr(module, "API_KEY", "token")

    calls = []

    def fake_request(path, connection=None, query=None):
        calls.append((path, connection, query))
        return 200, {"files": []}

    monkeypatch.setattr(module, "request", fake_request)

    output = run_main(
        module,
        [
            "--connection",
            "conn-9",
            "list-files",
            "--search",
            "name contains 'roadmap'",
            "--folder-id",
            "folder-123",
            "--page-size",
            "5",
            "--order-by",
            "modifiedTime desc",
            "--fields",
            "nextPageToken,files(id,name)",
        ],
    )
    payload = json.loads(output)

    assert payload == {"status": 200, "data": {"files": []}}
    assert calls == [
        (
            "/files",
            "conn-9",
            {
                "pageSize": 5,
                "fields": "nextPageToken,files(id,name)",
                "orderBy": "modifiedTime desc",
                "q": "name contains 'roadmap' and 'folder-123' in parents and trashed = false",
            },
        )
    ]


def test_shared_with_me_uses_drive_query_builder(module, monkeypatch):
    monkeypatch.setattr(module, "API_KEY", "token")

    calls = []

    def fake_request(path, connection=None, query=None):
        calls.append((path, connection, query))
        return 200, {"files": []}

    monkeypatch.setattr(module, "request", fake_request)

    run_main(module, ["shared-with-me", "--include-trashed", "--page-size", "3"])

    assert calls == [
        (
            "/files",
            None,
            {
                "pageSize": 3,
                "fields": module.DEFAULT_LIST_FIELDS,
                "q": "sharedWithMe = true",
            },
        )
    ]


def test_list_files_auto_enables_shared_drive_flags_with_drive_id(module):
    args = module.argparse.Namespace(
        page_size=10,
        fields="files(id,name)",
        page_token=None,
        order_by=None,
        spaces=None,
        corpora="drive",
        drive_id="drive-123",
        supports_all_drives=None,
        include_items_from_all_drives=None,
        search=None,
        folder_id=None,
        shared_with_me=False,
        include_trashed=False,
        query=[],
    )

    assert module.build_list_query(args) == {
        "pageSize": 10,
        "fields": "files(id,name)",
        "corpora": "drive",
        "driveId": "drive-123",
        "supportsAllDrives": "true",
        "includeItemsFromAllDrives": "true",
        "q": "trashed = false",
    }


def test_get_file_encodes_file_id_and_supports_extra_query(module, monkeypatch):
    monkeypatch.setattr(module, "API_KEY", "token")

    calls = []

    def fake_request(path, connection=None, query=None):
        calls.append((path, connection, query))
        return 200, {"id": "file/1"}

    monkeypatch.setattr(module, "request", fake_request)

    run_main(
        module,
        [
            "get-file",
            "file/1",
            "--supports-all-drives",
            "--query",
            "acknowledgeAbuse=true",
        ],
    )

    assert calls == [
        (
            "/files/file%2F1",
            None,
            {
                "fields": module.DEFAULT_FILE_FIELDS,
                "supportsAllDrives": "true",
                "acknowledgeAbuse": "true",
            },
        )
    ]
