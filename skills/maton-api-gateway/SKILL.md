---
name: maton-api-gateway
description: Use when you need a generic Maton gateway request helper for verified app routes instead of a service-specific Hermes wrapper.
version: 1.0.0
author: Nate Richardson + Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [maton, gateway, api, brokered-auth, http]
    related_skills: [maton-connections, maton-gmail, maton-google-calendar, maton-google-meet]
---

# Maton API Gateway

## Overview

This skill exposes a generic CLI for Maton's app gateway at `https://gateway.maton.ai`.
Use it when you already know the target app prefix and route shape, but you do not want to build a new one-off wrapper first.

It reuses the shared Maton HTTP helper layer used by the app-specific skills, including:

- bearer auth through `MATON_API_KEY`
- JSON request/response handling
- structured HTTP error output
- optional `Maton-Connection` targeting for multi-account cases

The command returns both the HTTP status and the fully constructed request URL so the exact route is inspectable.

See `references/apps-and-routes.md` for verified route families and examples.

## When to Use

Use this when:
- you need a generic GET/POST/PATCH/DELETE against a Maton gateway route
- you already know the app prefix such as `google-mail` or `google-calendar`
- you want to probe or extend beyond the narrow service-specific wrappers
- you need inspectable request construction before promoting a pattern into a dedicated skill

Avoid this when:
- you do not yet know the route shape or app prefix
- a service-specific skill already covers the task cleanly
- the operation is write-destructive and you have not validated payload shape first
- you have not confirmed which connected account should receive the request

## Requirements

```bash
export MATON_API_KEY=...
```

Optional:

```bash
export MATON_GATEWAY_BASE_URL=https://gateway.maton.ai
```

## Command Shape

```bash
python scripts/maton_api_gateway.py <get|post|patch|delete> \
  --app <app-prefix> \
  --path </provider-route> \
  [--query key=value ...] \
  [--body '{"json":true}' | --body @body.json] \
  [--connection <connection-id>]
```

Arguments:

- `--app` — Maton app prefix, such as `google-mail` or `google-calendar`
- `--path` — route suffix after the app prefix, such as `/gmail/v1/users/me/profile`
- `--query key=value` — repeat per query parameter; values are URL-encoded
- `--body` — inline JSON or `@file.json`; supported on `post`, `patch`, and `delete`
- `--connection` — optional explicit `Maton-Connection` header

## Quick Start

Verified GETs:

```bash
python scripts/maton_api_gateway.py get \
  --app google-mail \
  --path /gmail/v1/users/me/profile

python scripts/maton_api_gateway.py get \
  --app google-calendar \
  --path /calendar/v3/users/me/calendarList
```

With query params:

```bash
python scripts/maton_api_gateway.py get \
  --app google-mail \
  --path /gmail/v1/users/me/messages \
  --query maxResults=10 \
  --query q='is:unread in:inbox'
```

With an explicit connection:

```bash
python scripts/maton_api_gateway.py get \
  --connection <connection-id> \
  --app google-calendar \
  --path /calendar/v3/calendars/primary/events \
  --query maxResults=5 \
  --query singleEvents=true \
  --query orderBy=startTime
```

## Safe Usage Workflow

1. Start with `maton-connections` and identify the exact account you want.
2. Prefer a verified GET first so you can confirm route family and account targeting.
3. Inspect the returned `request.url` before assuming the route is correct.
4. Only move to `post`, `patch`, or `delete` after verifying the upstream API contract.
5. For writes, keep JSON payloads in a file when they are non-trivial.

## Output Shape

Success output:

```json
{
  "status": 200,
  "request": {
    "method": "GET",
    "url": "https://gateway.maton.ai/google-mail/gmail/v1/users/me/profile",
    "connection": null,
    "body": null
  },
  "data": {}
}
```

HTTP errors are emitted as structured JSON:

```json
{
  "status": 403,
  "error": {
    "message": "forbidden"
  }
}
```

## Known Verified Route Families

Verified in this repo today:

- `google-mail` + `/gmail/v1/...`
- `google-calendar` + `/calendar/v3/...`
- `google-drive` + `/drive/v3/...` for the metadata/search read surface
- `google-meet` + `/v2/...`

Detailed examples live in `references/apps-and-routes.md`.

## Common Pitfalls

1. **Forgetting that `--path` is appended after `--app`**
   `--app google-mail --path /gmail/v1/users/me/profile` becomes `/google-mail/gmail/v1/users/me/profile`.

2. **Writing to the wrong account**
   If several accounts are connected for the same app, omit `--connection` only when you truly want Maton's default resolution.

3. **Claiming support from a single 401/403/404 result**
   Auth errors prove the host is live, not that the route shape or payload is correct.

4. **Sending destructive writes without a dry run path**
   Start with a read endpoint or a minimal test object before broader mutations.

5. **Passing malformed query syntax**
   Each query parameter must be `key=value`. Repeat `--query` for additional params.

## Verification Checklist

- [ ] `python scripts/maton_api_gateway.py get --app google-mail --path /gmail/v1/users/me/profile` returns structured JSON
- [ ] `request.url` matches the intended app-prefixed route
- [ ] explicit `--connection` is used when account targeting matters
- [ ] at least one verified GET succeeds before using a write method
- [ ] mutation payload shape has been validated before `post`, `patch`, or `delete`
