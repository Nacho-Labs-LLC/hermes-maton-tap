---
name: maton-google-docs
description: Use when you want Hermes to inspect or update Google Docs through Maton's managed OAuth gateway instead of direct Google OAuth.
version: 1.0.0
author: Nate Richardson + Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [maton, google-docs, docs, google-workspace, brokered-auth]
    related_skills: [maton-connections, maton-api-gateway, maton-google-calendar]
---

# Maton Google Docs

## Overview

This skill wraps the Maton gateway route family for Google Docs using the same stdlib request/helper pattern already used by the tap's Gmail and Google Calendar skills.

Grounding level:
- `google-docs` is already listed as a valid Maton connection app in this repo's `maton-connections` skill.
- The route family and request shapes documented here are grounded in Maton's public `api-gateway-skill` reference for Google Docs: `/google-docs/v1/documents/...`.
- Local request construction is covered by repo tests.
- This repo change did **not** include live authenticated validation against a real Google Docs connection, so keep operational claims narrower than Gmail/Calendar.

Base pattern:

```text
https://gateway.maton.ai/google-docs/v1/documents/...
```

Use the `Maton-Connection` header when more than one Docs-capable Google account exists.

## When to Use

Use this when:
- the user already connected Google Docs in Maton
- you need to fetch a document payload through Maton without native Google OAuth setup
- you need a thin, inspectable wrapper around document create or `batchUpdate` flows
- you need explicit multi-account targeting

Avoid this when:
- the user has not confirmed a working `google-docs` connection yet
- you need guarantees about write semantics that have not been live-validated in this tap
- you should avoid exposing full document bodies in the current context

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
python scripts/maton_google_docs.py get <document-id>
python scripts/maton_google_docs.py create-document --title "Draft brief"
python scripts/maton_google_docs.py insert-text <document-id> --text "Hello" --index 1
python scripts/maton_google_docs.py replace-text <document-id> --match '{{name}}' --replace 'Ada'
```

With a specific connection:

```bash
python scripts/maton_google_docs.py --connection <connection-id> get <document-id>
```

## Commands

### Read flow

- `get <document-id>` → `GET /documents/{documentId}`

Useful escape hatch:

```bash
python scripts/maton_google_docs.py get <document-id> --query suggestionsViewMode=PREVIEW_SUGGESTIONS_ACCEPTED
```

### Write-oriented wrappers

These are implemented as explicit wrappers over the documented Google Docs API shapes, but they are only locally request-validated in this repo right now.

- `create-document --title ...` → `POST /documents`
- `batch-update <document-id> --payload ...` → `POST /documents/{documentId}:batchUpdate`
- `insert-text <document-id> --text ... [--index N | --append]` → focused `batchUpdate` helper
- `replace-text <document-id> --match ... --replace ...` → focused `batchUpdate` helper

Examples:

```bash
python scripts/maton_google_docs.py create-document --title "Meeting notes"

python scripts/maton_google_docs.py insert-text <document-id> \
  --text "Status update" \
  --append

python scripts/maton_google_docs.py batch-update <document-id> \
  --payload @requests.json
```

## Payload escape hatch

For fields not covered by first-class flags, merge or provide raw JSON request bodies:

```bash
python scripts/maton_google_docs.py create-document \
  --title "Brief" \
  --payload '{"documentStyle":{"marginTop":{"magnitude":72,"unit":"PT"}}}'

python scripts/maton_google_docs.py batch-update <document-id> \
  --payload '{"requests":[{"replaceAllText":{"containsText":{"text":"{{name}}","matchCase":true},"replaceText":"Ada"}}]}'
```

`batch-update` requires a JSON object with a non-empty top-level `requests` array.

## Recommended Workflow

1. Use `maton-connections` to confirm the target `google-docs` connection ID.
2. Start with `get` to confirm the document is reachable through Maton.
3. Prefer focused wrappers like `insert-text` or `replace-text` for common edits.
4. Use raw `batch-update` only when you already know the exact Google Docs request shape you need.
5. If you need a route not wrapped here, fall back to `maton-api-gateway` rather than guessing hidden behavior.

## Common Pitfalls

1. **Wrong account due to omitted connection header**
   If multiple Google accounts are connected, use `--connection`.

2. **Claiming live write verification that did not happen**
   This skill's local tests confirm request construction, not real upstream success.

3. **Sending malformed batchUpdate payloads**
   `batch-update` requires a non-empty `requests` array.

4. **Forgetting that Docs indices are position-sensitive**
   Use `get` first when you need exact insertion/replacement context.

## Verification Checklist

- [ ] `python scripts/maton_google_docs.py get <document-id>` returns HTTP 200 against a real connection
- [ ] target connection is confirmed before operational writes
- [x] local tests cover `get`, `create-document`, `batch-update`, `insert-text`, and `replace-text` request construction
- [x] repo lint/test/compile checks pass after adding the skill
