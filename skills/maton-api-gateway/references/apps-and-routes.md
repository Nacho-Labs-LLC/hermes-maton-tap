# Maton apps and route prefixes

## Verified route families

These are grounded in the existing repo wrappers plus prior live verification against Maton-backed data.

### Gmail

App prefix:

```text
google-mail
```

Verified route pattern:

```text
/google-mail/gmail/v1/...
```

Known-good GET examples:

```bash
python scripts/maton_api_gateway.py get \
  --app google-mail \
  --path /gmail/v1/users/me/profile

python scripts/maton_api_gateway.py get \
  --app google-mail \
  --path /gmail/v1/users/me/messages \
  --query maxResults=10 \
  --query q='is:unread in:inbox'
```

### Google Meet

App prefix:

```text
google-meet
```

Verified route pattern:

```text
/google-meet/v2/...
```

Known-good GET examples:

```bash
python scripts/maton_api_gateway.py get \
  --app google-meet \
  --path /v2/conferenceRecords

python scripts/maton_api_gateway.py get \
  --app google-meet \
  --path /v2/spaces/xyz789
```

Scope note:
- treat this as the verified Meet API/control-data plane only, not live join/transcription/browser-control capability

### Google Calendar

App prefix:

```text
google-calendar
```

Verified route pattern:

```text
/google-calendar/calendar/v3/...
```

Known-good GET examples:

```bash
python scripts/maton_api_gateway.py get \
  --app google-calendar \
  --path /calendar/v3/users/me/calendarList

python scripts/maton_api_gateway.py get \
  --app google-calendar \
  --path /calendar/v3/calendars/primary/events \
  --query maxResults=5 \
  --query singleEvents=true \
  --query orderBy=startTime \
  --query timeMin=2026-06-05T00:00:00Z \
  --query timeMax=2026-06-06T00:00:00Z
```

### Google Drive

App prefix:

```text
google-drive
```

Verified route pattern:

```text
/google-drive/drive/v3/...
```

Verified live surface in this repo today:
- `GET /drive/v3/about`
- `GET /drive/v3/files`
- `GET /drive/v3/files/{fileId}`
- query-driven variants of `GET /drive/v3/files` used by the metadata/search wrappers, including shared-with-me filtering

Known-good GET examples:

```bash
python scripts/maton_api_gateway.py get \
  --app google-drive \
  --path /drive/v3/about \
  --query fields=user,storageQuota

python scripts/maton_api_gateway.py get \
  --app google-drive \
  --path /drive/v3/files \
  --query pageSize=10 \
  --query q='trashed = false'

python scripts/maton_api_gateway.py get \
  --app google-drive \
  --path /drive/v3/files/<file-id>
```

Scope note:
- this repo's Drive wrapper is intentionally metadata-first; do not infer upload, download, or write coverage from these verified reads

## Documented route families not yet repo-live-validated

These are grounded in repo code/tests plus external Maton route references, but not yet in a successful live request from this repo's validation environment.

### Google Docs

App prefix:

```text
google-docs
```

Documented route pattern:

```text
/google-docs/v1/documents/...
```

Grounding note:
- this route family is documented in Maton's public `api-gateway-skill` reference and wrapped by this repo's `maton-google-docs` skill
- unlike Gmail/Calendar/Meet above, this repo has not yet live-validated Docs requests against a real account

Known request shapes:

```bash
python scripts/maton_api_gateway.py get \
  --app google-docs \
  --path /v1/documents/<document-id>

python scripts/maton_api_gateway.py post \
  --app google-docs \
  --path /v1/documents \
  --body '{"title":"Draft brief"}'

python scripts/maton_api_gateway.py post \
  --app google-docs \
  --path /v1/documents/<document-id>:batchUpdate \
  --body @requests.json
```

## Connection targeting

If Maton has multiple connected accounts for the same app, pass an explicit connection:

```bash
python scripts/maton_api_gateway.py get \
  --connection <connection-id> \
  --app google-mail \
  --path /gmail/v1/users/me/profile
```

This sets:

```text
Maton-Connection: <connection-id>
```

## Mutation shape example

This shape is useful for exploring a route when you already know the Maton-backed API contract, but the example below is not yet repo-verified end to end:

```bash
python scripts/maton_api_gateway.py post \
  --connection <connection-id> \
  --app google-calendar \
  --path /calendar/v3/calendars/primary/events \
  --body @event.json
```

Use mutation commands only after you have:

1. verified the exact route and payload shape against provider docs or an existing working client
2. confirmed the target account with `maton-connections`
3. accepted that Maton will forward the write to the live upstream service

## Other candidate Maton-backed apps seen in prior research but not yet repo-verified

Treat these as leads, not promises:

- Slack
- Notion
- HubSpot
- Outlook
- Search Console

Do not claim Hermes support for these until you verify route prefixes and successful requests.