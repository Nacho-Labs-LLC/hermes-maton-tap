from __future__ import annotations

import json
import urllib.error
import urllib.request

DEFAULT_TIMEOUT = 60


def require_api_key(api_key: str) -> None:
    if not api_key:
        raise SystemExit("MATON_API_KEY is not set")


def build_json_request(
    url: str,
    api_key: str,
    *,
    method: str = "GET",
    body: object | None = None,
    connection: str | None = None,
) -> urllib.request.Request:
    require_api_key(api_key)
    data = None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    if connection:
        headers["Maton-Connection"] = connection
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    return urllib.request.Request(url, data=data, headers=headers, method=method)


def decode_json_response(resp) -> dict | list:
    raw = resp.read().decode("utf-8", "ignore")
    return json.loads(raw) if raw else {}


def request_json(
    url: str,
    api_key: str,
    *,
    method: str = "GET",
    body: object | None = None,
    connection: str | None = None,
    urlopen=urllib.request.urlopen,
    timeout: int = DEFAULT_TIMEOUT,
):
    request = build_json_request(
        url,
        api_key,
        method=method,
        body=body,
        connection=connection,
    )
    with urlopen(request, timeout=timeout) as resp:
        return resp.status, decode_json_response(resp)


def print_http_error(exc: urllib.error.HTTPError) -> None:
    raw = exc.read().decode("utf-8", "ignore")
    try:
        payload = json.loads(raw)
    except Exception:
        payload = raw
    print(json.dumps({"status": exc.code, "error": payload}, indent=2))
