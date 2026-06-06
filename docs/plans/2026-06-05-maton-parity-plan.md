# Maton Parity Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Bring `/mnt/workspace/hermes-maton-tap` from a narrow draft tap to a publishable Hermes skill tap with a generic Maton gateway skill and practical parity on Google Calendar.

**Architecture:** Keep the repo as a lightweight Hermes skill tap with per-skill `SKILL.md` files and stdlib Python helpers. First harden the repo and extract shared Maton HTTP logic, then add a generic `maton-api-gateway` skill, then extend `maton-google-calendar` from read-only to CRUD + Meet support using the shared helper layer.

**Tech Stack:** Hermes skill tap layout, Python 3 stdlib (`argparse`, `json`, `urllib`), GitHub repo metadata, pytest, ruff, GitHub Actions.

---

## Ground truth from comparison

**OpenClaw / ClawHub currently has:**
- a generic Maton gateway skill (`api-gateway`)
- a Maton connection-management/UI integration skill (`maton-agent-tools`)
- a richer calendar skill documenting create/update/delete/Meet/invite flows

**Hermes repo currently has:**
- `maton-connections` (`list`, `get`, `create`, `delete`)
- `maton-gmail` (`profile`, `list`, `get`)
- `maton-google-calendar` (`calendars`, `upcoming`)
- no commits, no remote, no tests, no CI, no shared helper module

## Operating rules

- Keep runtime dependencies at zero unless a strong reason appears.
- Prefer shared helper modules over duplicated request code.
- Default non-GET operations to explicit confirmation language in docs and skill guidance.
- Do not promise Maton endpoint behavior without either existing ClawHub evidence or live verification.

---

## Phase 1 — Repo hardening and publish readiness

### Task 1: Add developer project metadata

**Objective:** Give the tap a minimal Python project skeleton for linting and testing without changing runtime behavior.

**Files:**
- Create: `pyproject.toml`
- Modify: `README.md`

**Steps:**
1. Create `pyproject.toml` with project metadata for `hermes-maton-tap`.
2. Add dev tool configuration for `ruff` and `pytest` only.
3. Add a short `Development` section to `README.md` with local commands.
4. Verify with:
   - `python -m compileall skills`
   - `python -m pytest --collect-only`

**Acceptance:**
- repo has a valid `pyproject.toml`
- `pytest --collect-only` runs even before full tests are added

### Task 2: Create shared Maton HTTP helper

**Objective:** Remove duplicated auth/request/error code from the three existing scripts.

**Files:**
- Create: `shared/__init__.py`
- Create: `shared/maton_http.py`
- Modify: `skills/maton-connections/scripts/maton_connections.py`
- Modify: `skills/maton-gmail/scripts/maton_gmail.py`
- Modify: `skills/maton-google-calendar/scripts/maton_calendar.py`

**Steps:**
1. Add `shared/maton_http.py` with helpers for:
   - base URL normalization
   - bearer auth header
   - optional `Maton-Connection` header
   - JSON request body encoding
   - JSON response parsing
   - normalized HTTP error handling
2. Update the three existing scripts to call the shared helper instead of direct `urllib` boilerplate.
3. Keep current CLI behavior unchanged.
4. Verify each script still prints `--help` successfully.

**Acceptance:**
- all three scripts import shared helper code
- duplicated request code is removed
- existing commands still parse and run

### Task 3: Add test scaffolding and smoke coverage

**Objective:** Establish a minimal safety net before expanding functionality.

**Files:**
- Create: `tests/test_maton_connections.py`
- Create: `tests/test_maton_gmail.py`
- Create: `tests/test_maton_calendar.py`
- Create: `tests/test_maton_http.py`

**Steps:**
1. Add tests for missing `MATON_API_KEY` behavior.
2. Add tests for CLI parsing of each existing subcommand.
3. Mock `urllib.request.urlopen` or the shared helper boundary for 200 and 4xx responses.
4. Add one test covering `Maton-Connection` header injection.
5. Verify with `pytest -q`.

**Acceptance:**
- tests cover current skills before new features land
- a failing HTTP response produces structured JSON output and non-zero exit

### Task 4: Add CI and repo hygiene

**Objective:** Make the tap shippable and harder to regress.

**Files:**
- Create: `.github/workflows/ci.yml`
- Modify: `.gitignore`
- Modify: `README.md`

**Steps:**
1. Add CI for:
   - Python setup
   - `python -m compileall skills shared`
   - `ruff check .`
   - `pytest -q`
2. Ensure `.gitignore` excludes `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`.
3. Add a `Status` / `Roadmap` note in `README.md`.

**Acceptance:**
- clean local run mirrors CI
- repo no longer feels like an untracked scratch dir

---

## Phase 2 — Generic gateway parity

### Task 5: Add `maton-api-gateway` skill skeleton

**Objective:** Create the missing generic cross-app Maton gateway skill.

**Files:**
- Create: `skills/maton-api-gateway/SKILL.md`
- Create: `skills/maton-api-gateway/scripts/maton_api_gateway.py`
- Modify: `README.md`

**Steps:**
1. Create the new skill directory and frontmatter.
2. Describe safe usage rules in `SKILL.md`:
   - require named app/account/task context
   - start with GET/list calls
   - use `Maton-Connection` when multiple accounts exist
   - document explicit caution for non-GET calls
3. Build `maton_api_gateway.py` supporting:
   - `get`
   - `post`
   - `patch`
   - `delete`
   - `--app`
   - `--path`
   - `--query key=value`
   - `--body @file.json` or inline JSON
   - `--connection`
4. Reuse `shared/maton_http.py`.

**Acceptance:**
- Hermes gains a generic Maton gateway skill instead of only app-specific wrappers
- request construction is explicit and inspectable

### Task 6: Add app routing reference for the generic gateway

**Objective:** Make the generic gateway usable without guessing route shapes.

**Files:**
- Create: `skills/maton-api-gateway/references/apps-and-routes.md`
- Modify: `skills/maton-api-gateway/SKILL.md`
- Modify: `README.md`

**Steps:**
1. Document route prefix patterns already evidenced by current repo and ClawHub research:
   - Gmail: `/google-mail/gmail/v1/...`
   - Calendar: `/google-calendar/calendar/v3/...`
2. Add a “known-good examples” section for:
   - Gmail message listing
   - Calendar event listing
   - one generic non-GET example shape with caution notes
3. Add candidate app list from ClawHub research:
   - Slack
   - Notion
   - HubSpot
   - Outlook
   - Drive
   - Search Console
4. Explicitly mark unverified examples as unverified.

**Acceptance:**
- users can understand route shape without reverse engineering the repo
- docs separate verified from aspirational coverage

---

## Phase 3 — Calendar parity

### Task 7: Expand the shared helper for write operations

**Objective:** Support POST/PATCH/DELETE cleanly before extending calendar commands.

**Files:**
- Modify: `shared/maton_http.py`
- Modify: `tests/test_maton_http.py`

**Steps:**
1. Ensure helper supports arbitrary HTTP methods.
2. Add optional JSON body support.
3. Add query-string builder support.
4. Add tests for POST/PATCH/DELETE request construction.

**Acceptance:**
- helper fully supports calendar CRUD needs

### Task 8: Upgrade `maton-google-calendar` to CRUD + Meet support

**Objective:** Close the biggest service-specific parity gap versus ClawHub.

**Files:**
- Modify: `skills/maton-google-calendar/scripts/maton_calendar.py`
- Modify: `skills/maton-google-calendar/SKILL.md`
- Modify: `tests/test_maton_calendar.py`

**Target commands:**
- keep `calendars`
- keep `upcoming`
- add `list-events` (alias-friendly replacement for `upcoming`)
- add `create-event`
- add `update-event`
- add `reschedule-event`
- add `update-attendees`
- add `delete-event`

**Endpoint mappings:**
- `GET /users/me/calendarList`
- `GET /calendars/{calendarId}/events`
- `POST /calendars/{calendarId}/events`
- `PATCH /calendars/{calendarId}/events/{eventId}`
- `DELETE /calendars/{calendarId}/events/{eventId}`

**Steps:**
1. Implement `list-events` while preserving `upcoming` compatibility.
2. Implement `create-event` with summary/start/end/time-zone.
3. Extend `create-event` for attendees and `sendUpdates`.
4. Extend `create-event` for Google Meet via `conferenceDataVersion=1` and `conferenceData.createRequest`.
5. Implement `update-event` for partial field updates.
6. Implement `reschedule-event` as a thin ergonomic wrapper over PATCH.
7. Implement `update-attendees` as a focused PATCH wrapper.
8. Implement `delete-event`.
9. Add tests for command parsing and payload construction.

**Acceptance:**
- Hermes calendar skill reaches practical parity with the ClawHub calendar surface
- no duplicated request code is reintroduced

---

## Phase 4 — Documentation, verification, and release

### Task 9: Normalize README and installation story

**Objective:** Turn the repo into a clear public-facing tap.

**Files:**
- Modify: `README.md`

**Steps:**
1. Replace placeholder `OWNER/REPO` examples once the GitHub destination exists.
2. Add a skill matrix table:
   - skill
   - current capability
   - status (`verified`, `partial`, `planned`)
3. Add a short roadmap section:
   - current
   - next
   - later
4. Add exact local validation commands.

**Acceptance:**
- an external Hermes user can understand what is ready today
- README does not oversell parity that does not exist

### Task 10: Verify endpoint/base-URL assumptions

**Objective:** Resolve documentation drift between Maton hostnames before release claims.

**Files:**
- Modify: `README.md`
- Modify: relevant `SKILL.md` files if needed
- Optional: create `docs/research/maton-endpoints.md`

**Steps:**
1. Validate whether these are all valid and current:
   - `https://ctrl.maton.ai`
   - `https://gateway.maton.ai`
   - `https://api.maton.ai`
2. Decide whether Hermes should keep split base URLs or standardize.
3. Update docs to reflect verified truth only.

**Acceptance:**
- repo docs do not conflict with researched ClawHub guidance

### Task 11: Prepare first public release

**Objective:** Ship a clean initial version after parity work lands.

**Files:**
- Modify: `README.md`
- Optional: create `CHANGELOG.md`

**Steps:**
1. Make first commit history coherent.
2. Tag a version after tests pass.
3. Confirm install flow from a clean Hermes environment.
4. Publish or point Hermes at the GitHub tap.

**Acceptance:**
- repo is installable as a Hermes tap without hand-holding

---

## Suggested owner map

- **Platform/Core:** Tasks 2, 5, 6, 7
- **Integrations:** Task 8
- **DevTools/Release:** Tasks 1, 3, 4, 9, 11
- **Research/Verification:** Task 10

## Minimum viable milestone

Call the repo meaningfully upgraded once these are done:
- Tasks 1–5
- Task 8 (at least create/update/delete without Meet if Meet lags)
- Task 9
- Task 10

That gets the tap from draft to useful.

## Verification commands

Run from repo root:

```bash
python -m compileall skills shared
python -m pytest -q
ruff check .
python skills/maton-connections/scripts/maton_connections.py --help
python skills/maton-gmail/scripts/maton_gmail.py --help
python skills/maton-google-calendar/scripts/maton_calendar.py --help
python skills/maton-api-gateway/scripts/maton_api_gateway.py --help
```

## Final recommendation

Build in this order:
1. repo hardening
2. shared helper
3. generic `maton-api-gateway`
4. calendar CRUD parity
5. docs + release cleanup

That sequence closes the biggest strategic gap first without creating more duplicated code.
