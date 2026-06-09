# Security, Compliance, And Operations

## 1. Security Principles

- Public traffic enters only through Nginx in domain server production
  environment.
- Local production environment should bind services to localhost or a private
  LAN address.
- Internal services bind to loopback/private network.
- Secrets stay outside Git.
- High-risk actions require owner confirmation.
- Audit logs are mandatory for important actions.
- External runtimes are isolated behind adapters.
- Memory promotion is reviewed.

## 2. Secret Handling

Never commit:

- model API keys;
- PostgreSQL passwords;
- Feishu secrets;
- WeChat credentials;
- QQ tokens;
- QR/session state;
- SSH private keys;
- generated media with private content.

Use server-side environment files and permission-restricted config paths.

In local production environment, secrets may live on the private machine, but they still
must use restricted files and must not be copied into the repository, Obsidian
notes, screenshots, or exported reports.

In domain server production environment, secrets must stay on the server and
public callback routes must expose only the exact platform-required paths.

## 3. Audit Requirements

Audit:

- login and admin access;
- connector inbound events;
- outgoing platform messages;
- job state transitions;
- approval requests;
- approval decisions;
- memory promotions;
- simulation runs;
- external source retrieval;
- deployment changes.

## 4. Backup Requirements

Back up:

- PostgreSQL;
- Obsidian vault;
- Hermes data;
- release artifacts;
- Nginx config;
- non-secret config templates.

Test restore before claiming production readiness.

## 5. Operations Checks

Required checks:

- service health;
- database migration status;
- disk space;
- PostgreSQL backup freshness;
- queue depth;
- connector callback errors;
- model provider failures;
- search runtime health;
- memory write-back errors;
- audit log write failures.

## 6. Server Management Telemetry Boundary

The commercial platform may collect only operational metadata by default:

- server identity;
- license identity and status;
- Hermes version;
- health, database, backup, and connector readiness states;
- aggregate error counters;
- last heartbeat timestamp.

The platform must not collect customer prompts, generated answers, uploaded
files, Obsidian note bodies, memory content, raw private logs, credentials, or
database dumps unless the customer explicitly triggers a redacted diagnostic
bundle.

## 7. Commercial Compliance

Before commercial release:

- review external project licenses;
- preserve required attribution;
- avoid copying GPL code into proprietary modules;
- isolate GPL runtimes when used;
- document data retention;
- document owner approval rules;
- document incident response.
