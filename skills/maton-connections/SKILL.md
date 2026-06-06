---
name: maton-connections
description: Use when you need to inspect or manage Maton OAuth connections from Hermes instead of setting up duplicate native OAuth.
version: 1.0.0
author: Nate Richardson + Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [maton, oauth, gmail, calendar, brokered-auth, connections]
    related_skills: [maton-gmail, maton-google-calendar]
---

# Maton Connections

## Overview

Use Maton as the auth broker instead of redoing provider OAuth inside Hermes.
This skill handles the Maton control plane at `https://ctrl.maton.ai` so you can list,
create, inspect, and delete connections for apps like Gmail and Google Calendar.

This is the right first step when a user says they already authenticated accounts in Maton.

## When to Use

Use this when:
- the user already has app auth set up in Maton
- you need to verify what accounts/apps are connected
- you need a connection ID for multi-account targeting
- you need to create a new Maton connection link

Do not use this for reading mailbox contents or calendar events directly. Use the service-specific skills for that.

## Requirements

Set:

```bash
export MATON_API_KEY=...
```

Optional:

```bash
export MATON_BASE_URL=https://ctrl.maton.ai
```

## Quick Start

```bash
python scripts/maton_connections.py list
python scripts/maton_connections.py list --app google-mail
python scripts/maton_connections.py get <connection-id>
python scripts/maton_connections.py create google-calendar
```

## Recommended Workflow

1. List active connections.
2. Identify the target app and account.
3. Save or note the `connection_id` you want.
4. Pass that ID through the `Maton-Connection` header when using a gateway-backed skill.

## Common App Names

- `google-mail`
- `google-calendar`
- `google-drive`
- `google-docs`
- `google-meet`
- `linkedin`
- `dropbox`
- `google-search-console`

## Example

```bash
python scripts/maton_connections.py list --app google-mail --status ACTIVE
```

## Common Pitfalls

1. **No `MATON_API_KEY` set**
   The script will fail immediately. Put the key in `.env` or export it for the shell.

2. **Assuming one account only**
   Maton can hold several active Gmail or Calendar connections. Always inspect the account metadata before acting.

3. **Treating connection visibility as service capability**
   A visible connection only proves auth exists. It does not mean you already built the read/write wrapper on top of it.

## Verification Checklist

- [ ] `python scripts/maton_connections.py list` returns HTTP 200
- [ ] target app appears in the response
- [ ] target account email or metadata matches the intended account
- [ ] chosen `connection_id` is recorded before using a service-specific skill
