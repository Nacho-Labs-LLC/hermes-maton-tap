---
name: maton-google-calendar
description: Use when you want Hermes to read or modify Google Calendar through Maton's managed OAuth gateway instead of direct Google OAuth.
version: 1.0.0
author: Nate Richardson + Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [maton, calendar, google-calendar, scheduling, brokered-auth]
    related_skills: [maton-connections, maton-gmail]
---

# Maton Google Calendar

## Overview

This skill uses Maton's Google Calendar gateway endpoint instead of direct Google OAuth.
It covers practical day-planning reads plus the common event mutation flows needed for a real scheduling assistant.

Base pattern:

```text
https://gateway.maton.ai/google-calendar/calendar/v3/...
```

Use the `Maton-Connection` header when more than one calendar account exists.

## When to Use

Use this when:
- the user already connected Google Calendar in Maton
- you need a sane near-future event view without hand-building OAuth flows
- you need to create, update, reschedule, invite, or delete events through the Maton gateway
- you need explicit multi-account targeting

Avoid this when:
- you have not verified the target connection
- you need unsupported Calendar features you have not live-tested through Maton
- the user wants direct Google OAuth or native Google SDK behavior instead of Maton's brokered path

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
python scripts/maton_calendar.py calendars
python scripts/maton_calendar.py upcoming --max-results 10
python scripts/maton_calendar.py list-events --calendar-id primary --time-min 2026-06-05T00:00:00Z --time-max 2026-06-06T00:00:00Z
python scripts/maton_calendar.py create-event --summary "1:1" --start 2026-06-05T15:00:00Z --end 2026-06-05T15:30:00Z
python scripts/maton_calendar.py reschedule-event abc123 --start 2026-06-05T16:00:00Z --end 2026-06-05T16:30:00Z
python scripts/maton_calendar.py delete-event abc123
```

With a specific connection:

```bash
python scripts/maton_calendar.py --connection <connection-id> upcoming
```

## Commands

### Read flows

- `calendars` — list visible calendars
- `upcoming` — ergonomic near-future list view
- `list-events` — same endpoint as `upcoming`, but named for broader event-listing workflows

Both `upcoming` and `list-events` call `GET /calendars/{calendarId}/events`.
By default they inject `timeMin=<now in UTC>` when you did not provide `--time-min`, so the default user path shows current/near-future items instead of ancient recurring instances.
Use `--include-past` when you intentionally want historical events with no auto-applied lower bound.

Useful flags:

```bash
--calendar-id primary
--max-results 10
--time-min 2026-06-05T00:00:00Z
--time-max 2026-06-06T00:00:00Z
--include-past
--show-deleted
--query key=value        # repeatable extra query params
```

### Mutation flows

- `create-event` → `POST /calendars/{calendarId}/events`
- `update-event` → `PATCH /calendars/{calendarId}/events/{eventId}`
- `reschedule-event` → focused PATCH wrapper for start/end changes
- `update-attendees` → focused PATCH wrapper for attendee replacement/clearing
- `delete-event` → `DELETE /calendars/{calendarId}/events/{eventId}`

Core create example:

```bash
python scripts/maton_calendar.py create-event \
  --calendar-id primary \
  --summary "Project review" \
  --start 2026-06-05T18:00:00Z \
  --end 2026-06-05T18:30:00Z \
  --time-zone UTC \
  --attendee person@example.com \
  --send-updates all
```

Partial update example:

```bash
python scripts/maton_calendar.py update-event evt_123 \
  --summary "Project review (moved)" \
  --start 2026-06-05T19:00:00Z \
  --end 2026-06-05T19:30:00Z \
  --time-zone UTC
```

Attendee replacement example:

```bash
python scripts/maton_calendar.py update-attendees evt_123 \
  --attendee a@example.com \
  --attendee b@example.com \
  --send-updates externalOnly
```

Delete example:

```bash
python scripts/maton_calendar.py delete-event evt_123 --send-updates all
```

## Attendees, payloads, and Google Meet

Attendees are supported with repeated `--attendee email@example.com` flags on create/update flows.
To clear attendees entirely, use:

```bash
python scripts/maton_calendar.py update-attendees evt_123 --clear-attendees
```

For fields not covered by first-class flags, merge a JSON object into the generated request body:

```bash
python scripts/maton_calendar.py update-event evt_123 \
  --payload '{"extendedProperties":{"private":{"source":"hermes"}}}'

python scripts/maton_calendar.py create-event ... --payload @body.json
```

For extra query params, repeat `--query key=value`.
This is the escape hatch for Maton/Google Calendar parameters the wrapper does not expose directly.

Google Meet support is available through `conferenceData.createRequest`:

```bash
python scripts/maton_calendar.py create-event \
  --summary "Client call" \
  --start 2026-06-05T20:00:00Z \
  --end 2026-06-05T20:30:00Z \
  --add-meet \
  --send-updates all
```

When `--add-meet` is used, the helper automatically adds `conferenceDataVersion=1` unless you already supplied it via `--query`, and it generates a request ID unless you provide `--meet-request-id`.

## Practical Workflow

1. Use `maton-connections` to find the correct calendar connection ID.
2. Run `calendars` to verify account visibility.
3. Start with `upcoming` or `list-events` and let the default near-future `timeMin` keep results sane.
4. When mutating, prefer the focused wrappers first (`reschedule-event`, `update-attendees`) before arbitrary patch payloads.
5. Use `--payload` and repeatable `--query` only when the first-class flags are not enough.

## Common Pitfalls

1. **Wrong account due to omitted connection header**
   Multiple Google accounts can make implicit defaults misleading. Use `--connection` when precision matters.

2. **Expecting historical results from the default `upcoming` path**
   The default now uses `timeMin=<current UTC time>` for practical near-future behavior. Add explicit `--time-min` or `--include-past` when you want older events.

3. **Patching an event with no actual fields**
   `update-event` exits if you do not provide any change fields or payload.

4. **Forgetting attendee notifications or conference data query params**
   Use `--send-updates` intentionally, and use `--add-meet` so `conferenceDataVersion=1` is set for Meet creation.

5. **Assuming every Google Calendar field has a first-class flag**
   Use `--payload` for niche fields instead of editing the script ad hoc.

## Verification Checklist

- [ ] `python scripts/maton_calendar.py calendars` returns 200
- [ ] `python scripts/maton_calendar.py upcoming` returns current/near-future events by default, not ancient recurring items
- [ ] `list-events` works with explicit `--time-min/--time-max` when the date window matters
- [ ] `create-event`, `update-event`, `reschedule-event`, `update-attendees`, and `delete-event` all construct the expected request shape in tests
- [ ] target connection is confirmed before using mutation results operationally
