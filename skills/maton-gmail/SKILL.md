---
name: maton-gmail
description: Use when you want Hermes to read or inspect Gmail through Maton's managed OAuth gateway instead of native Google OAuth.
version: 1.0.0
author: Nate Richardson + Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [maton, gmail, email, google-mail, brokered-auth]
    related_skills: [maton-connections, maton-google-calendar]
---

# Maton Gmail

## Overview

This skill uses Maton's Gmail gateway endpoint instead of direct Google OAuth.
It is the Hermes-side equivalent of the old OpenClaw Maton Gmail workflow, rebuilt
for Hermes as a reusable skill.

Base pattern:

```text
https://gateway.maton.ai/google-mail/gmail/v1/...
```

Auth is always:

```text
Authorization: Bearer $MATON_API_KEY
```

If several Gmail accounts are connected, set the target account with:

```text
Maton-Connection: <connection-id>
```

## When to Use

Use this when:
- the user already connected Gmail in Maton
- you need to inspect inbox state without direct Google OAuth setup
- you need quick mailbox reads in a Hermes session
- you need explicit multi-account targeting

Avoid this when:
- the user has not connected Gmail in Maton yet
- you need unsupported Gmail features you have not verified through the gateway
- you should avoid exposing mailbox contents in the current context

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
python scripts/maton_gmail.py profile
python scripts/maton_gmail.py list --max-results 10 --query 'is:unread'
python scripts/maton_gmail.py get <message-id> --format metadata
```

With a specific connection:

```bash
python scripts/maton_gmail.py list --connection <connection-id> --query 'is:unread in:inbox'
```

## Practical Workflow

1. Use `maton-connections` to find the correct Gmail connection ID.
2. Start with `profile` to confirm the target account.
3. List messages with a narrow query.
4. Fetch individual message details only when needed.

## Common Queries

- `is:unread`
- `is:unread in:inbox`
- `from:person@example.com`
- `after:2026/01/01`
- `has:attachment`

## Common Pitfalls

1. **Wrong mailbox due to omitted connection header**
   If multiple Gmail connections exist, the default may not be the one you intended.

2. **Pulling too much mail into context**
   Start with narrow queries and metadata-first reads.

3. **Claiming send/write support without testing**
   The gateway may support more endpoints, but verify them before telling a user they work in Hermes.

## Verification Checklist

- [ ] `python scripts/maton_gmail.py profile` returns 200
- [ ] email address matches the intended mailbox
- [ ] `list` works with a narrow query
- [ ] message fetch works for at least one ID before relying on the skill operationally
