# Hermes Backend Runtime

## 1. Role

Hermes is the single backend authority.

It owns:

- API contracts;
- route planning;
- async jobs;
- connector-neutral social turn planning;
- media delivery planning;
- model gateway calls;
- PostgreSQL persistence;
- memory candidate governance;
- Obsidian write-back;
- EverOS memory bridge;
- MiroFish simulation bridge;
- TrendRadar and SearXNG adapters;
- owner approval gates;
- audit logging.

## 2. Runtime Architecture

```text
HTTP API
  -> request validation
  -> channel policy
  -> route planner
  -> job manager
  -> tool/adapters
  -> PostgreSQL persistence
  -> response contract
```

The HTTP layer can remain lightweight while the product is being rebuilt. The
domain model should be written so that the HTTP adapter can later migrate to
FastAPI without rewriting business logic.

## 3. Module Boundaries

Recommended modules:

- `server`: HTTP adapter.
- `config`: environment and typed runtime settings.
- `db`: PostgreSQL connection and migrations.
- `jobs`: durable job service.
- `routing`: route classification.
- `social_turn`: quick ACK, direct reply, slow job planning.
- `media_delivery`: send-image/upload/text-fallback decision.
- `connectors`: Feishu, WeChat, QQ client boundaries.
- `memory`: Obsidian and EverOS bridge.
- `intelligence`: TrendRadar, SearXNG, crawl, model gateway.
- `simulation`: MiroFish brief and run service.
- `approvals`: owner confirmation gates.
- `audit`: immutable event recording.

## 4. API Readiness States

Every feature reports one of:

- `ready`
- `partial`
- `missing_config`
- `disabled`
- `planned`

The frontend must never infer readiness from hidden secrets or optimistic UI
state.

## 5. Job Lifecycle

Slow tasks use a durable lifecycle:

```text
queued
  -> acknowledged
  -> running
  -> completed
  -> delivered
```

Failure path:

```text
queued/running
  -> failed
  -> failure_delivered
```

Every transition writes:

- job row update;
- job_event row;
- audit event when user-visible or risky;
- connector delivery status when applicable.

## 6. Owner Confirmation

Owner confirmation is required for:

- company write actions;
- legal/contract wording;
- HR or compensation changes;
- payment or financial decisions;
- external promises;
- destructive file or data operations;
- memory promotion when confidence is low or content is sensitive.

The system may draft, summarize, simulate, and recommend. It must not silently
execute high-risk actions.

