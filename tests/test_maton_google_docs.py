from __future__ import annotations

import json

import pytest
from conftest import run_main


@pytest.fixture
def module(load_module):
    return load_module(
        "skills/maton-google-docs/scripts/maton_google_docs.py",
        "maton_google_docs_under_test",
    )


def test_request_requires_api_key(module, monkeypatch):
    monkeypatch.setattr(module, "API_KEY", "")

    with pytest.raises(SystemExit, match="MATON_API_KEY is not set"):
        module.request("GET", "/documents/doc-1")


def test_get_builds_document_path_and_query(module, monkeypatch):
    monkeypatch.setattr(module, "API_KEY", "token")

    calls = []

    def fake_request(method, path, **kwargs):
        calls.append((method, path, kwargs))
        return 200, {"documentId": "doc-1"}

    monkeypatch.setattr(module, "request", fake_request)

    output = run_main(
        module,
        [
            "--connection",
            "conn-7",
            "get",
            "doc/1",
            "--query",
            "suggestionsViewMode=PREVIEW_SUGGESTIONS_ACCEPTED",
        ],
    )
    payload = json.loads(output)

    assert payload == {"status": 200, "data": {"documentId": "doc-1"}}
    assert calls == [
        (
            "GET",
            "/documents/doc%2F1",
            {
                "connection": "conn-7",
                "query": {"suggestionsViewMode": "PREVIEW_SUGGESTIONS_ACCEPTED"},
            },
        )
    ]


def test_create_document_merges_payload(module, monkeypatch):
    monkeypatch.setattr(module, "API_KEY", "token")

    calls = []

    def fake_request(method, path, **kwargs):
        calls.append((method, path, kwargs))
        return 200, {"documentId": "doc-2"}

    monkeypatch.setattr(module, "request", fake_request)

    run_main(
        module,
        [
            "create-document",
            "--title",
            "Draft brief",
            "--payload",
            '{"tabsCriteria":{"tabIds":["tab-1"]}}',
        ],
    )

    assert calls == [
        (
            "POST",
            "/documents",
            {
                "connection": None,
                "body": {"title": "Draft brief", "tabsCriteria": {"tabIds": ["tab-1"]}},
                "query": {},
            },
        )
    ]


def test_batch_update_requires_requests_array(module):
    args = type("Args", (), {"payload": '{"writeControl": {}}'})()

    with pytest.raises(SystemExit, match="non-empty requests array"):
        module.build_batch_update_body(args)


def test_insert_text_supports_append(module, monkeypatch):
    monkeypatch.setattr(module, "API_KEY", "token")

    calls = []

    def fake_request(method, path, **kwargs):
        calls.append((method, path, kwargs))
        return 200, {"replies": []}

    monkeypatch.setattr(module, "request", fake_request)

    run_main(
        module,
        [
            "insert-text",
            "doc-3",
            "--text",
            "Hello, world!",
            "--append",
        ],
    )

    assert calls == [
        (
            "POST",
            "/documents/doc-3:batchUpdate",
            {
                "connection": None,
                "body": {
                    "requests": [
                        {
                            "insertText": {
                                "endOfSegmentLocation": {},
                                "text": "Hello, world!",
                            }
                        }
                    ]
                },
                "query": {},
            },
        )
    ]


def test_replace_text_supports_match_case_toggle(module, monkeypatch):
    monkeypatch.setattr(module, "API_KEY", "token")

    calls = []

    def fake_request(method, path, **kwargs):
        calls.append((method, path, kwargs))
        return 200, {"replies": []}

    monkeypatch.setattr(module, "request", fake_request)

    run_main(
        module,
        [
            "replace-text",
            "doc-4",
            "--match",
            "{{name}}",
            "--replace",
            "Ada",
            "--no-match-case",
        ],
    )

    assert calls == [
        (
            "POST",
            "/documents/doc-4:batchUpdate",
            {
                "connection": None,
                "body": {
                    "requests": [
                        {
                            "replaceAllText": {
                                "containsText": {
                                    "text": "{{name}}",
                                    "matchCase": False,
                                },
                                "replaceText": "Ada",
                            }
                        }
                    ]
                },
                "query": {},
            },
        )
    ]
