---
name: maton-google-drive
description: Use when you want Hermes to inspect Google Drive metadata through Maton's managed OAuth gateway instead of direct Google OAuth.
version: 1.0.0
author: Nate Richardson + Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [maton, google-drive, drive, files, brokered-auth]
    related_skills: [maton-connections, maton-api-gateway]
---

# Maton Google Drive

## Overview

This skill provides a practical read-oriented Google Drive surface on top of Maton's gateway pattern.
It intentionally focuses on metadata and search/list flows first:

- account/Drive capability summary via `about`
- file listing and search via `list-files`
- shared file triage via `shared-with-me`
- single-file metadata via `get-file`

Base pattern used by the wrapper:

```text
https://gateway.maton.ai/google-drive/drive/v3/...
```

This route family now has repo live-validation evidence for the metadata/search surface this skill wraps: `GET /drive/v3/about`, `GET /drive/v3/files`, and `GET /drive/v3/files/{fileId}` via the `google-drive` app prefix.
Keep claims scoped to that metadata-first surface; this skill still does **not** claim upload, download, or write coverage.

## When to Use

Use this when:
- the user already connected Google Drive in Maton
- you need to inspect Drive files or folders without setting up direct Google OAuth
- you want a quick metadata/search surface in a Hermes session
- you need explicit multi-account targeting with `--connection`

Avoid this when:
- the target Drive connection has not been confirmed
- you need binary downloads, uploads, permission writes, or other semantics not wrapped here
- you need to promise Drive behaviors beyond the verified metadata/search reads documented here

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
python scripts/maton_drive.py about
python scripts/maton_drive.py list-files --page-size 10
python scripts/maton_drive.py list-files --search "name contains 'roadmap'"
python scripts/maton_drive.py shared-with-me --page-size 10
python scripts/maton_drive.py get-file <file-id>
```

With a specific connection:

```bash
python scripts/maton_drive.py --connection <connection-id> list-files --page-size 10
```

## Commands

### `about`

Calls `GET /about` and defaults `fields` to:

```text
user,storageQuota,importFormats,exportFormats,maxUploadSize
```

Example:

```bash
python scripts/maton_drive.py about --fields user,storageQuota
```

### `list-files`

Calls `GET /files` and is optimized for practical search/list workflows.
By default it adds `q=trashed = false` unless you pass `--include-trashed`.

Useful flags:

```bash
--page-size 25
--page-token <token>
--order-by modifiedTime desc
--fields nextPageToken,files(id,name,mimeType)
--search "name contains 'roadmap'"
--folder-id <folder-id>
--shared-with-me
--spaces drive
--corpora drive
--drive-id <shared-drive-id>
--supports-all-drives
--include-items-from-all-drives
--query key=value
```

Examples:

```bash
python scripts/maton_drive.py list-files \
  --search "mimeType contains 'image/'" \
  --order-by modifiedTime desc \
  --page-size 20

python scripts/maton_drive.py list-files \
  --folder-id <folder-id> \
  --fields nextPageToken,files(id,name,webViewLink)
```

### `shared-with-me`

Also calls `GET /files`, but automatically adds `sharedWithMe = true` to the Drive query expression.
It is just an ergonomic wrapper over `list-files`.

Example:

```bash
python scripts/maton_drive.py shared-with-me --page-size 20
```

### `get-file`

Calls `GET /files/{fileId}` for a single file's metadata.
The default `fields` set is richer than the list view and includes name, MIME type, timestamps, owners, links, and some sharing flags.

Example:

```bash
python scripts/maton_drive.py get-file <file-id> \
  --fields id,name,mimeType,owners(displayName,emailAddress),webViewLink
```

## Shared drives and query composition

When `--drive-id` is supplied on list flows, the helper auto-enables:

- `supportsAllDrives=true`
- `includeItemsFromAllDrives=true`

unless you explicitly override them with the boolean flags.

The Drive `q` expression is composed from the first-class flags in this order:

1. `--search`
2. `--folder-id` → `'folder-id' in parents`
3. `--shared-with-me` → `sharedWithMe = true`
4. default `trashed = false` unless `--include-trashed`

For anything not exposed as a first-class flag, repeat `--query key=value`.

## Practical Workflow

1. Use `maton-connections` to find the correct `google-drive` connection.
2. Start with `about` to confirm the account responds.
3. Use `list-files` with a narrow `--search` or `--folder-id`.
4. Use `get-file` only for the specific file you care about.
5. If you need a niche Drive parameter not surfaced here, try `--query key=value` or fall back to `maton-api-gateway` for exploratory work.

## Common Pitfalls

1. **Wrong Drive account due to omitted connection header**
   If multiple Google accounts are connected, use `--connection` explicitly.

2. **Over-broad search results**
   Start with `--search`, `--folder-id`, or smaller `--page-size` values.

3. **Assuming content download or mutation support from this wrapper**
   This skill intentionally stays metadata-first. It does not claim upload/download/write coverage.

4. **Forgetting shared-drive flags**
   Shared-drive queries often need `driveId` plus all-drives parameters. This helper auto-enables the common combination when `--drive-id` is set.

## Verification Checklist

- [ ] `python scripts/maton_drive.py about` returns 200 on the target Drive-backed Maton connection
- [ ] `list-files` returns the expected file subset for at least one narrow query
- [ ] `shared-with-me` or equivalent `list-files` filtering returns the expected shared subset when applicable
- [ ] `get-file` returns metadata for a known file ID
- [ ] target connection is confirmed before relying on results operationally
