# Commercial Productization Roadmap

## 1. Phase A: Documentation Reset

Status target:

- old explanatory docs removed;
- phase reports preserved;
- product documentation rebuilt by function;
- PostgreSQL selected for production;
- server rebuild strategy documented.

Acceptance:

- README points only to the new documentation set;
- `reports/` remains intact;
- no stale docs continue to describe the old architecture as current.

## 2. Phase B: Server Rebuild Foundation

Build:

- `/opt/moxi-os` layout;
- local production environment and domain server production environment mode
  switch;
- PostgreSQL;
- Hermes deployment;
- Nginx routes;
- environment templates;
- backup path;
- smoke checks.
- one-command usable deployment scripts.

Acceptance:

- clean server boot;
- local production environment boots without public DNS;
- domain server production environment verifies domain, HTTPS, and callback
  paths;
- database migration table exists;
- Hermes reads PostgreSQL;
- frontend can call Hermes.
- deploy command prints working health, ready, and capabilities URLs.

## 3. Phase C: Durable Runtime State

Build:

- PostgreSQL job store;
- job events;
- audit logs;
- approval table;
- connector event metadata;
- source refs.

Acceptance:

- async jobs survive process restart;
- audit log records all connector-visible lifecycle events;
- owner approval queue is queryable.

## 4. Phase D: Memory Product Layer

Build:

- EverOS internal service;
- Hermes EverOS client;
- memory candidates table;
- Obsidian inbox write-back;
- owner review and promotion flow.

Acceptance:

- one conversation summary enters EverOS;
- one memory candidate enters PostgreSQL;
- one reviewed note is written to Obsidian.

## 5. Phase E: Intelligence Layer

Build:

- TrendRadar adapter;
- `/hotspots`;
- source refs;
- SearXNG optional adapter;
- report write-back.

Acceptance:

- one trend item appears in UI;
- one source-backed report enters Obsidian;
- sources are tracked in PostgreSQL.

## 6. Phase F: Company Surface

Build:

- Feishu identity mapping;
- read-only task/doc/Bitable flows;
- approval cards;
- daily and evening reports.

Acceptance:

- real Feishu group retest passes;
- one company risk is detected;
- no write action happens without owner approval.

## 7. Phase G: Simulation Layer

Build:

- simulation brief template;
- MiroFish adapter;
- simulation run table;
- Obsidian simulation report write-back.

Acceptance:

- one project decision simulation completes;
- one market scenario simulation completes;
- owner decision note is created only after confirmation.

## 8. Phase H: Commercial Hardening

Build:

- release procedure;
- CI gates;
- backup restore test;
- license review;
- monitoring;
- incident response;
- customer-safe deployment checklist.

Acceptance:

- clean release can be deployed from source;
- rollback is documented and tested;
- no stale demo-only backend remains in production path.
