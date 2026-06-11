# hermes-maton-tap

Hermes skill tap for using [Maton](https://maton.ai) as a brokered auth gateway.

It gives Hermes a practical, reusable surface for Maton-backed Google and related app workflows without rebuilding native OAuth flows inside Hermes.

This repo is meant to be published as a GitHub skill tap so other Hermes users can add it with:

```bash
hermes skills tap add Nacho-Labs-LLC/hermes-maton-tap
```

## Install skills from the tap

Install only the skill(s) you need:

```bash
hermes skills install Nacho-Labs-LLC/hermes-maton-tap/skills/maton-connections
hermes skills install Nacho-Labs-LLC/hermes-maton-tap/skills/maton-api-gateway
hermes skills install Nacho-Labs-LLC/hermes-maton-tap/skills/maton-gmail
hermes skills install Nacho-Labs-LLC/hermes-maton-tap/skills/maton-google-calendar
hermes skills install Nacho-Labs-LLC/hermes-maton-tap/skills/maton-google-docs
hermes skills install Nacho-Labs-LLC/hermes-maton-tap/skills/maton-google-drive
hermes skills install Nacho-Labs-LLC/hermes-maton-tap/skills/maton-google-meet
```

## Included skills

| Skill | Install path | Purpose |
| --- | --- | --- |
| `maton-connections` | `Nacho-Labs-LLC/hermes-maton-tap/skills/maton-connections` | Inspect and manage Maton connections for brokered OAuth accounts. |
| `maton-api-gateway` | `Nacho-Labs-LLC/hermes-maton-tap/skills/maton-api-gateway` | Send generic GET/POST/PATCH/DELETE requests through verified Maton gateway route families. |
| `maton-gmail` | `Nacho-Labs-LLC/hermes-maton-tap/skills/maton-gmail` | Read Gmail through Maton's managed gateway. |
| `maton-google-calendar` | `Nacho-Labs-LLC/hermes-maton-tap/skills/maton-google-calendar` | List calendars, inspect upcoming events, and perform common event CRUD/invite flows. |
| `maton-google-docs` | `Nacho-Labs-LLC/hermes-maton-tap/skills/maton-google-docs` | Inspect and update Google Docs through a thin Maton wrapper with documented route grounding, request-shape tests, and intentionally narrower live-claim language. |
| `maton-google-drive` | `Nacho-Labs-LLC/hermes-maton-tap/skills/maton-google-drive` | Inspect Google Drive metadata/search flows through a live-validated, metadata-first wrapper. |
| `maton-google-meet` | `Nacho-Labs-LLC/hermes-maton-tap/skills/maton-google-meet` | Inspect verified Google Meet conference records/participants and create/get Meet spaces. |

Each skill ships its own `SKILL.md` with usage guidance, requirements, examples, and pitfalls.

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

## Quick start

```bash
# Add the tap
hermes skills tap add Nacho-Labs-LLC/hermes-maton-tap

# Install the minimum useful set
hermes skills install Nacho-Labs-LLC/hermes-maton-tap/skills/maton-connections
hermes skills install Nacho-Labs-LLC/hermes-maton-tap/skills/maton-gmail
hermes skills install Nacho-Labs-LLC/hermes-maton-tap/skills/maton-google-calendar

# Make sure Hermes can see your Maton auth
export MATON_API_KEY=...
```

Recommended first use:
1. load `maton-connections`
2. confirm the target account/connection ID
3. use a service-specific skill like Gmail, Calendar, Drive, Docs, or Meet

## Best fit

This tap is strongest when:
- Maton already owns your app auth
- you want Hermes to operate across multiple connected Google accounts
- you want thin, inspectable wrappers instead of a heavy SDK or native OAuth rebuild


## Status

Current state: **beta but practically usable**.

Live verification status captured in this repo:
- Confirmed against real Maton-backed data: connection listing, Gmail profile/list/get, Google Calendar calendar listing, and current event listing with explicit time bounds
- Confirmed route families for the generic gateway helper: `google-mail` + `/gmail/v1/...`, `google-calendar` + `/calendar/v3/...`, and `google-meet` + `/v2/...`
- Confirmed real mutation flows against a temporary validation event on a live calendar: generic gateway `POST`, generic gateway `PATCH`, generic gateway `DELETE`, plus calendar `create-event`, `update-event`, `reschedule-event`, `update-attendees --clear-attendees`, and `--add-meet`
- Confirmed Google Meet live capability surface for this tap: `GET /v2/conferenceRecords`, `GET /v2/conferenceRecords/{id}`, `GET /v2/conferenceRecords/{id}/participants`, `POST /v2/spaces`, and `GET /v2/spaces/{space}`
- Confirmed Google Docs live read capability for this tap: `GET /google-docs/v1/documents/{documentId}` against real Maton Docs connections; write-oriented Docs helpers remain request-shape-tested but not yet live write-validated
- Calendar default UX tightened: `upcoming` / `list-events` now default `timeMin` to the current UTC time so the common path surfaces near-future events instead of ancient recurring instances
- Confirmed Google Drive live capability surface for this tap's metadata-first wrapper: `GET /drive/v3/about`, `GET /drive/v3/files`, and `GET /drive/v3/files/{fileId}` via the `google-drive` app prefix

Known limits:
- Verified live coverage is currently grounded in Gmail, Google Calendar, Google Drive metadata/search flows, and the narrow Google Meet conference-records/spaces surface
- Google Docs is currently live-validated for the `get` read path; write-oriented helpers remain documented/request-test-validated in-repo but not yet live write-validated in this tap
- Google Drive is intentionally metadata-first here; download/upload/write semantics are not claimed by this wrapper
- Do not claim live Google Meet join/transcription/browser-control capability from this repo; Meet here is the API/control-data plane only
- Attendee notification behavior to third parties was **not** exhaustively live-tested; keep public framing honest about that
- Additional in-flight skill work should not be advertised until the relevant files, docs, and tests land in the tracked repo state

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

### Local validation

Preferred validation commands from the repo root:

```bash
python3 -m compileall maton_http.py skills tests
.venv/bin/pytest --collect-only
.venv/bin/pytest -q
.venv/bin/ruff check .
uv build --sdist --wheel
```

The repo currently assumes either an existing `.venv` with `pytest` and `ruff`, or a local tool runner such as `uv`.

### Optional isolated environment

```bash
python3 -m venv .venv
. .venv/bin/activate
uv pip install --python .venv/bin/python -e '.[dev]'
```

### Packaging notes

- `pyproject.toml` carries the project metadata and dev extra.
- `MANIFEST.in` keeps the source distribution honest by shipping the skill docs/scripts, docs, tests, and shared helper module.
- `uv build --sdist --wheel` is the release-readiness packaging smoke test.

## Publish and review checklist

Before calling the tap ready for review:

1. Run the local validation commands above.
2. Confirm the README skill list matches the currently tracked `skills/` directories.
3. Keep beta framing and verified-scope notes honest.
4. Clean local build artifacts before commit if you generated them.
5. Use the fuller checklist in [`docs/release-checklist.md`](docs/release-checklist.md).

## Repository layout

```text
.
├── README.md
├── pyproject.toml
├── MANIFEST.in
├── maton_http.py
├── docs/
├── skills/
└── tests/
```

## Notes

This repo was rebuilt from working OpenClaw-era Maton skill references and live verification against Maton endpoints, not copied blindly.
