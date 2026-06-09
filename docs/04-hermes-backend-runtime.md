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
- `platform`: commercial platform heartbeat and server-management metadata.

## 4. API Readiness States

Every feature reports one of:

- `ready`
- `partial`
- `missing_config`
- `disabled`
- `planned`

The frontend must never infer readiness from hidden secrets or optimistic UI
state.

## 5. Platform Heartbeat

Hermes exposes:

```text
GET /platform/heartbeat
```

The endpoint returns operational metadata for the bairui platform or a local
server-agent:

- protocol version;
- server id;
- organization id;
- license id and status;
- Hermes version;
- aggregate health status;
- PostgreSQL readiness status;
- backup readiness placeholder;
- connector readiness summary;
- 24-hour error count placeholder;
- `bairui` brand key;
- generation timestamp.

The heartbeat must not include customer business data, prompts, conversation
messages, Obsidian note bodies, memory content, file content, model API keys, or
connector secrets.

## 6. Job Lifecycle

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

## 7. Owner Confirmation

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
