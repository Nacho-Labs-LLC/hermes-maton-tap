from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import pathlib
import sys
import urllib.error
from email.message import Message

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


@pytest.fixture
def load_module():
    def _load(relative_path: str, module_name: str):
        path = ROOT / relative_path
        spec = importlib.util.spec_from_file_location(module_name, path)
        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    return _load


class FakeJsonResponse:
    def __init__(self, payload: dict | list, status: int = 200):
        self.status = status
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def run_main(module, argv: list[str]):
    stdout = io.StringIO()
    old_argv = sys.argv
    sys.argv = [module.__file__, *argv]
    try:
        with contextlib.redirect_stdout(stdout):
            module.main()
    finally:
        sys.argv = old_argv
    return stdout.getvalue()


def run_main_expect_exit(module, argv: list[str]):
    stdout = io.StringIO()
    old_argv = sys.argv
    sys.argv = [module.__file__, *argv]
    try:
        with contextlib.redirect_stdout(stdout):
            try:
                module.main()
            except SystemExit as exc:
                return exc.code, stdout.getvalue()
    finally:
        sys.argv = old_argv

    raise AssertionError("expected SystemExit")


def make_http_error(code: int, payload):
    if isinstance(payload, (dict, list)):
        body = json.dumps(payload).encode("utf-8")
    else:
        body = str(payload).encode("utf-8")
    return urllib.error.HTTPError(
        url="https://example.test",
        code=code,
        msg="error",
        hdrs=Message(),
        fp=io.BytesIO(body),
    )
