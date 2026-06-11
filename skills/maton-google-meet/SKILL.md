---
name: maton-google-meet
description: Use when you want Hermes to inspect Google Meet conference records or create/get Meet spaces through Maton's managed OAuth gateway instead of direct Google OAuth.
version: 1.0.0
author: Nate Richardson + Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [maton, google-meet, meet, conferencing, brokered-auth]
    related_skills: [maton-connections, maton-api-gateway, maton-google-calendar]
---

# Maton Google Meet

## Overview

This skill uses Maton's Google Meet gateway endpoint instead of direct Google OAuth.
It is intentionally scoped to the Google Meet routes already verified live in Maton:

- `GET /v2/conferenceRecords`
- `GET /v2/conferenceRecords/{id}`
- `GET /v2/conferenceRecords/{id}/participants`
- `POST /v2/spaces`
- `GET /v2/spaces/{space}`

Base pattern:

```text
https://gateway.maton.ai/google-meet/v2/...
```

Use the `Maton-Connection` header when more than one Google Meet account exists.

This skill does not claim live support for joining meetings, browser control, live transcription, captions, recording control, or any other real-time session automation.
It is for the verified records/spaces API and control-data plane only.

## When to Use

Use this when:
- the user already connected Google Meet in Maton
- you need to inspect existing conference records or participant lists
- you need to create a Meet space through Maton's brokered gateway
- you need explicit multi-account targeting for Google Meet data

Avoid this when:
- you have not verified the target connection
- the task requires live meeting participation or in-call automation
- you need unsupported Google Meet features that have not been verified through Maton
- the user wants direct Google OAuth or a native Google SDK flow instead of Maton's brokered path

## Requirements

```bash
export MATON_API_KEY=...
```

Optional:

```bash
export MATON_GATEWAY_BASE_URL=https://gateway.maton.ai
```

## Quick Start

```bash
python scripts/maton_google_meet.py list-records
python scripts/maton_google_meet.py get-record abc123
python scripts/maton_google_meet.py participants abc123
python scripts/maton_google_meet.py create-space
python scripts/maton_google_meet.py get-space xyz789
```

With a specific connection:

```bash
python scripts/maton_google_meet.py --connection <connection-id> list-records
```

## Commands

### Read flows

- `list-records` — `GET /v2/conferenceRecords`
- `get-record <record_id>` — `GET /v2/conferenceRecords/{id}`
- `participants <record_id>` — `GET /v2/conferenceRecords/{id}/participants`
- `get-space <space>` — `GET /v2/spaces/{space}`

Useful flags:

```bash
--connection <connection-id>
--page-size 10
--query key=value
```

Examples:

```bash
python scripts/maton_google_meet.py list-records --page-size 5
python scripts/maton_google_meet.py participants conferenceRecords/abc123 --page-size 20
python scripts/maton_google_meet.py get-space spaces/xyz789
```

`--query` is repeatable and is the escape hatch for upstream query parameters not promoted to first-class flags by this wrapper.

### Create-space flow

- `create-space` — `POST /v2/spaces`

Default usage:

```bash
python scripts/maton_google_meet.py create-space
```

With an explicit JSON payload:

```bash
python scripts/maton_google_meet.py create-space \
  --payload '{"config":{"accessType":"OPEN"}}'

python scripts/maton_google_meet.py create-space --payload @space.json
```

The helper sends `{}` when you omit `--payload`, which keeps the common path simple while still allowing explicit JSON bodies for advanced cases.

## Practical Workflow

1. Use `maton-connections` to find the correct `google-meet` connection ID.
2. Start with `list-records` or `get-space` to confirm account targeting.
3. Use `participants` only after confirming the target conference record ID.
4. Use `create-space` for the verified space-creation flow.
5. If you need anything beyond the verified records/spaces surface, drop to `maton-api-gateway` only after verifying the route shape independently.

## Common Pitfalls

1. **Overclaiming Google Meet capability**
   This wrapper is intentionally narrow. Do not present it as live join, transcription, browser automation, or meeting-host control.

2. **Wrong account due to omitted connection header**
   Multiple Google accounts can make implicit defaults misleading. Use `--connection` when precision matters.

3. **Confusing full resource names with bare IDs**
   Pass the resource identifier exactly as expected by the upstream route, such as `conferenceRecords/...` or `spaces/...`, and let the helper URL-encode it.

4. **Assuming every upstream option has a dedicated CLI flag**
   Use repeated `--query key=value` for GET calls and `--payload` for `create-space` instead of editing the script ad hoc.

5. **Treating existence of a connection as proof of runtime features**
   A visible `google-meet` connection proves auth exists. It does not prove support for unverified meeting-control operations.

## Verification Checklist

- [ ] `python scripts/maton_google_meet.py list-records` returns 200
- [ ] `get-record` works against a real conference record ID
- [ ] `participants` works against a real conference record ID
- [ ] `create-space` and `get-space` succeed against a real Meet-backed connection when you need to rely on them operationally
- [ ] target connection is confirmed before treating returned records or spaces as authoritative
