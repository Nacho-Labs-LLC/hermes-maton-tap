# hermes-maton-tap

Hermes skill tap for using [Maton](https://maton.ai) as a brokered auth gateway.

This repo is meant to be published as a GitHub skill tap so other Hermes users can add it with:

```bash
hermes skills tap add OWNER/REPO
```

Then install individual skills such as:

```bash
hermes skills install OWNER/REPO/skills/maton-connections
hermes skills install OWNER/REPO/skills/maton-api-gateway
hermes skills install OWNER/REPO/skills/maton-gmail
hermes skills install OWNER/REPO/skills/maton-google-calendar
```

## What this is

A clean Hermes-friendly packaging of the Maton workflow Nate was already using in OpenClaw:
- control-plane connection management via `https://ctrl.maton.ai`
- app gateway requests via `https://gateway.maton.ai`
- explicit multi-account support via the `Maton-Connection` header

## What this is not

- Not a Hermes core plugin
- Not a Maton SDK
- Not a full wrapper for every Maton-backed app yet

It is a skill tap with helper scripts that make the existing Maton auth actually usable from Hermes sessions.

## Included skills

- `maton-connections` — list/create/get/delete connections in Maton
- `maton-api-gateway` — generic GET/POST/PATCH/DELETE helper for app-prefixed Maton gateway routes
- `maton-gmail` — read Gmail through Maton gateway
- `maton-google-calendar` — list calendars, surface sane near-future events by default, and perform common event CRUD/invite flows through Maton gateway

## Status

Current state: **beta but practically usable**. The repo has project scaffolding for linting/testing/CI, a generic Maton gateway helper, and a Google Calendar skill that covers both read flows and common event mutations.

Live verification status:
- Confirmed against real Maton-backed data: connection listing, Gmail profile/list/get, Google Calendar calendar listing, and current event listing with explicit time bounds
- Confirmed route families for the generic gateway helper: `google-mail` + `/gmail/v1/...` and `google-calendar` + `/calendar/v3/...`
- Confirmed real mutation flows against a temporary validation event on a live calendar: generic gateway `POST`, generic gateway `PATCH`, generic gateway `DELETE`, plus calendar `create-event`, `update-event`, `reschedule-event`, `update-attendees --clear-attendees`, and `--add-meet`
- Calendar default UX tightened: `upcoming` / `list-events` now default `timeMin` to the current UTC time so the common path surfaces near-future events instead of ancient recurring instances
- Local verification is green: `compileall`, `pytest --collect-only`, `pytest`, and `ruff check .`

Known limits:
- Verified live coverage is currently grounded in Gmail + Google Calendar only
- Attendee notification behavior to third parties was **not** exhaustively live-tested; keep public framing honest about that
- The main remaining product roadmap item is broader live validation and expansion beyond the currently verified Maton app set

## Roadmap

- Current: publish the tap cleanly with honest beta framing and verified-scope notes
- Current: shared Maton HTTP helpers plus a generic Maton gateway skill are in place
- Next: expand verified Maton coverage beyond Gmail and Google Calendar
- Later: promote additional generic gateway patterns into dedicated app skills as real usage proves them out

## Environment

All skills expect:

```bash
export MATON_API_KEY=...
```

Optional overrides:

```bash
export MATON_BASE_URL=https://ctrl.maton.ai
export MATON_GATEWAY_BASE_URL=https://gateway.maton.ai
```

## Development

Local validation commands:

```bash
python -m compileall skills tests
python -m pytest --collect-only
python -m pytest -q
python -m ruff check .
```

If you want an isolated local environment:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -U pytest ruff
```

## Publish checklist

1. Create a GitHub repo
2. Push this directory
3. Tell users to run `hermes skills tap add owner/repo`
4. Install a skill with `hermes skills install owner/repo/skills/<skill-slug>`

## Notes

This repo was rebuilt from working OpenClaw-era Maton skill references and live verification against Maton endpoints, not copied blindly.
