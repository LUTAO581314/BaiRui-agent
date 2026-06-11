# Backend Contract Freeze For Frontend

Status: frozen for first frontend integration pass.

This document freezes the backend contract that the first `bairui` frontend
must integrate before deeper visual and interaction work begins. It is derived
from the current `/frontend/contract` output and the implemented backend/CLI.

The purpose is to prevent frontend rework: the frontend should connect to these
surfaces as stable product boundaries instead of reading raw files, guessing
state names, or exposing internal runtime/source project details.

## 1. Freeze Rules

- Public product brand is only `bairui`.
- The frontend must start by reading `GET /frontend/contract`.
- The frontend must render missing configuration, blockers, partial readiness,
  and owner-review states honestly.
- The frontend must not read runtime data files directly.
- The frontend must not expose secrets, internal paths, runtime tokens, vendor
  repository names, or non-`bairui` product brands.
- Any external write, channel send, memory promotion, or risky action must stay
  owner-reviewed.
- Channels are currently plan, diagnostics, approval, and audit only. They do
  not dispatch to external services.
- If an endpoint returns `missing_config`, `blocked`, `needs_review`, or
  `approval_required`, the frontend must disable optimistic success actions.

## 2. Stable Entry Points

The frontend integration starts with:

- `GET /frontend/contract`
- `GET /health`
- `GET /ready`
- `GET /runtime/readiness`
- `GET /events`

The CLI equivalent for contract inspection is:

```bash
python -m src.hermes frontend-contract
```

The current contract version is:

```text
2026-06-11.4
```

## 3. Frozen Screens

### Activation

Purpose: guide first-time setup to a truthful usable state.

Reads:

- `GET /frontend/contract`
- `GET /health`
- `GET /ready`
- `GET /runtime/readiness`
- `GET /license`
- `GET /platform/heartbeat`

Actions:

- `POST /chat`

Required flow:

1. Brand Lock
2. Runtime Health
3. License And Platform
4. Model Gateway
5. Document Runtime
6. Memory Review
7. Reports And Sources

Frontend rule: do not show a final ready state while a blocking activation step
is incomplete.

### Dashboard

Purpose: one-screen operational truth.

Reads:

- `GET /health`
- `GET /ready`
- `GET /runtime/readiness`
- `GET /capabilities`
- `GET /platform/heartbeat`
- `GET /jobs`
- `GET /audit`
- `GET /events`

Actions:

- `POST /jobs`

### Command

Purpose: controlled chat/task entry with honest model readiness.

Reads:

- `GET /capabilities`
- `GET /memory/status`

Actions:

- `POST /chat`

Frontend rule: when model configuration is missing, keep the send action
disabled or show the exact missing configuration state.

### Documents

Purpose: commercial document ingestion workbench.

Reads:

- `POST /document/parse/session-list`
- `POST /document/parse/session-summary`

Actions:

- `POST /document/parse/ingest-plan`
- `POST /document/parse/workbench-next`
- `POST /document/parse/workbench-run-until-blocked`

Related inspection endpoints:

- `GET /document/ingests`
- `GET /document/ingest-runs`
- `GET /document/artifacts`
- `GET /document/index-runs`
- `GET /document/ingest-reports`

Frontend rule: show the pipeline as a stepper or checklist. If the next action
returns `needs_review`, route the user to Memory Review instead of pretending
the workflow completed.

### Memory Review

Purpose: prevent uncontrolled long-term memory writes.

Reads:

- `POST /document/parse/memory-review-pending`
- `GET /document/memory-candidates`
- `GET /document/memory-reviews`

Actions:

- `POST /document/parse/review-memory-candidate`
- `POST /document/parse/memory-review-batch`

Frontend rule: approvals and rejections must be explicit owner decisions. Do
not auto-promote memory candidates.

### Reports

Purpose: inspect generated reports and source evidence.

Reads:

- `GET /document/ingest-reports`
- `GET /source-refs`

Actions:

- `POST /obsidian/reports`

Frontend rule: report chrome and empty states must expose only `bairui`.

### Channels

Purpose: connector-style control surface with owner approval.

Reads:

- `GET /channels/status`
- `GET /channels/targets`
- `GET /channels/diagnostics`
- `GET /channels/approvals`
- `GET /events`

Actions:

- `POST /channels/send`
- `POST /channels/approvals/review`

Frontend rule: this is an approval queue, not a sender. Even after review, the
backend records `will_send=false`. The UI must not show sent/success delivery
states.

### Settings

Purpose: capability and runtime configuration status without secret exposure.

Reads:

- `GET /memory/status`
- `GET /voice/asr/status`
- `GET /document/parse/status`
- `GET /intel/status`
- `GET /simulation/status`
- `GET /search/status`
- `GET /index/status`

Actions: none in the first frontend integration pass.

## 4. Frozen API Groups

### Operations

- `GET /jobs`
- `POST /jobs`
- `GET /audit`
- `GET /events`
- `GET /platform/heartbeat`

### Document Workbench

- `POST /document/parse/session-list`
- `POST /document/parse/session-summary`
- `POST /document/parse/workbench-state`
- `POST /document/parse/workbench-next`
- `POST /document/parse/workbench-run-until-blocked`

### Memory Review

- `POST /document/parse/memory-review-pending`
- `POST /document/parse/review-memory-candidate`
- `POST /document/parse/memory-review-batch`

### Channels

- `GET /channels/status`
- `GET /channels/targets`
- `GET /channels/diagnostics`
- `GET /channels/approvals`
- `POST /channels/send`
- `POST /channels/approvals/review`

### Runtime Status

- `GET /capabilities`
- `GET /runtime/readiness`
- `GET /memory/status`
- `GET /document/parse/status`
- `GET /index/status`
- `GET /search/status`
- `GET /voice/asr/status`

## 5. Frozen Form Schemas

The frontend should render these forms from `/frontend/contract` rather than
hard-coding fields.

### chat_message

- `prompt`: textarea, required
- `system`: textarea, optional

### job_create

- `title`: text, optional
- `prompt`: textarea, required
- `route`: select, optional, one of `general`, `research`, `document`,
  `operations`

### document_ingest_plan

- `input_path`: file_path, required
- `title`: text, optional
- `output_dir`: directory_path, optional
- `backend`: select, optional
- `language`: text, optional
- `device`: select, optional, one of `cpu`, `cuda`

### document_workbench_step

- `ingest_id`: id, required
- `timeout_seconds`: number, optional

### document_workbench_run

- `ingest_id`: id, required
- `timeout_seconds`: number, optional
- `max_steps`: number, optional

### memory_review_decision

- `candidate_id`: id, required
- `decision`: segmented, required, one of `approve`, `reject`
- `note`: textarea, optional

### memory_review_batch

- `candidate_ids`: id_list, required
- `decision`: segmented, required, one of `approve`, `reject`
- `resume_after_review`: toggle, optional

### report_write

- `title`: text, optional
- `body`: textarea, required

### channel_send

- `target_id`: select, required, sourced from `/channels/targets`
- `media_kind`: segmented, required, one of `text`, `image`, `video`, `file`
- `text`: textarea, optional
- `attachment_path`: file_path, optional
- `owner_confirmation`: toggle, required

### channel_approval_review

- `request_id`: id, required
- `decision`: segmented, required, one of `approve`, `reject`
- `note`: textarea, optional

## 6. Frozen State Values

The frontend must handle these states without crashing or hiding them:

- `ready`
- `partial`
- `blocked`
- `missing_config`
- `not_found`
- `completed`
- `failed`
- `needs_review`
- `step_limit_reached`
- `approval_required`
- `unsupported_media`
- `pending_review`
- `reviewed`
- `already_reviewed`

Suggested UI mapping:

- `ready`, `completed`: positive
- `partial`, `needs_review`, `approval_required`, `pending_review`: attention
- `missing_config`, `blocked`, `failed`, `unsupported_media`: blocking or error
- `not_found`, `already_reviewed`, `step_limit_reached`: neutral warning

## 7. Frozen Event Types

`GET /events` returns snapshot SSE frames projected from audit records.

Known frontend event types include:

- `job.created`
- `document.step.planned`
- `document.step.completed`
- `memory.review.required`
- `memory.review.completed`
- `report.created`
- `command.completed`
- `command.blocked`
- `channel.send.approval_required`
- `channel.send.blocked`
- `channel.approval.requested`
- `channel.approval.reviewed`
- `system.changed`
- `audit.event`

Frontend rule: unknown event types must render as a generic audit event, not
crash the event panel.

## 8. Frozen CLI Surface

The first frontend pass does not need to call CLI commands directly, but the
CLI is the backend operator equivalent and must stay aligned with the API.

Core commands:

```bash
python -m src.hermes status
python -m src.hermes capabilities
python -m src.hermes frontend-contract
python -m src.hermes runtime-readiness
python -m src.hermes events
python -m src.hermes channels status
python -m src.hermes channels targets
python -m src.hermes channels diagnostics
python -m src.hermes channels approvals --pending
python -m src.hermes channels plan-send --target-id owner_review --text "Review this update"
python -m src.hermes channels review-approval --request-id <request_id> --decision approve
python -m src.hermes document parse session-list --limit 50
python -m src.hermes document parse session-summary --ingest-id <ingest_id>
python -m src.hermes document parse workbench-next --ingest-id <ingest_id>
python -m src.hermes document parse workbench-run-until-blocked --ingest-id <ingest_id>
```

## 9. Brand And Safety Freeze

The frontend must not expose these classes of information:

- non-`bairui` public product names;
- upstream project names in customer-facing route labels, headings, buttons,
  empty states, setup copy, report chrome, or activation text;
- raw secrets or secret-like values;
- local filesystem secret paths;
- internal runtime tokens, ports, container names, or upstream endpoints;
- external send success when the backend only recorded approval.

Allowed public brand fields:

- `bairui`
- `brand_key: bairui`
- `trademark: bairui`
- `logo_text: bairui`

## 10. Frontend Implementation Order

Use this order for the first source-UI customization pass:

1. App shell, route map, and `bairui` brand replacement.
2. API client generated around `/frontend/contract` groups.
3. Activation screen.
4. Dashboard and event panel.
5. Documents workbench.
6. Memory Review.
7. Reports.
8. Channels diagnostics and approvals.
9. Command.
10. Settings.

Do not start with decorative polish. First make the product console truthful,
connected, and brand-clean.

## 11. Contract Change Policy

After this freeze:

- additive endpoints may be added;
- existing endpoint paths should not be renamed during the first frontend pass;
- existing state values should not be removed;
- existing form field names should not be changed without updating this file,
  `/frontend/contract`, tests, and frontend code together;
- customer-visible copy must remain `bairui` only.

