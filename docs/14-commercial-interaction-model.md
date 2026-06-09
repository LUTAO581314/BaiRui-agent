# Commercial Interaction Model

## 1. Product Interaction Goal

MOXI Industrial Agent OS should feel like a controlled operating layer, not a
single chat window.

The commercial interaction model must support:

- chat command;
- dashboard inspection;
- approval decisions;
- memory review;
- company workflow;
- source-backed research;
- simulation;
- deployment and operations visibility.

## 2. User Roles

### Owner

The owner can:

- configure the system;
- approve risky actions;
- promote memory;
- inspect audit logs;
- start simulations;
- connect company channels;
- decide deployment mode.

### Company Operator

The company operator can:

- ask about tasks, customers, reports, risks, and documents;
- receive reminders;
- view generated summaries;
- request actions that require owner approval.

The operator cannot approve high-risk actions unless explicitly granted in a
future permission model.

### Personal User

The personal user surface supports:

- reminders;
- quick capture;
- low-risk companion replies;
- daily summaries.

Personal channels cannot execute company, financial, HR, legal, or irreversible
actions.

### Admin

The admin surface supports:

- deployment state;
- capability state;
- logs;
- backup status;
- connector health;
- database migration status.

## 3. Primary Surfaces

### MOXI / Brain UI

Primary product surface:

- chat;
- job progress;
- capability dashboard;
- memory candidates;
- approvals;
- simulation reports;
- settings;
- admin status.

### Feishu

Company operation surface:

- task summaries;
- document and table questions;
- company alerts;
- owner approval cards;
- daily and evening reports.

### WeChat

Personal surface:

- personal reminders;
- quick capture;
- lightweight conversation;
- selected important alerts.

### QQ

Social surface:

- personal or community interaction;
- low-risk reminders;
- no company-write authority.

### CLI

Operator and development surface:

- deploy;
- verify;
- inspect;
- run migrations;
- export audit;
- debug local production.

## 4. Core User Journeys

### Journey A: First Usable Deployment

1. User clones repository.
2. User runs one deploy command.
3. Script creates `.env` and local secrets.
4. Script starts PostgreSQL and Hermes.
5. Script waits for `/health`.
6. Script prints usable URLs.
7. User opens status endpoints or Brain UI.

Success:

- no manual service assembly;
- no secret committed;
- no fake readiness.

### Journey B: Daily Company Briefing

1. Scheduled Hermes job reads configured company sources.
2. Hermes summarizes delays, risks, missing updates, and priorities.
3. Full report writes to Obsidian.
4. Short summary sends to Feishu.
5. High-risk suggested actions become approval requests.

Success:

- company summary is useful;
- sources are traceable;
- risky actions wait for owner confirmation.

### Journey C: Memory Review

1. Chat, report, or research creates memory candidates.
2. EverOS helps extract possible facts.
3. Hermes stores candidate metadata in PostgreSQL.
4. MOXI / Brain UI shows candidates.
5. Owner promotes, rejects, edits, or defers.
6. Promoted memory writes to Obsidian.

Success:

- memory improves without becoming noisy;
- owner can inspect and correct it.

### Journey D: Research And Intelligence

1. User asks for a topic.
2. Hermes chooses TrendRadar, SearXNG, or crawl API.
3. Sources are stored.
4. Model gateway synthesizes with citations.
5. Full report writes to Obsidian.
6. Short answer returns to the user.

Success:

- answer separates evidence from inference;
- report is durable;
- sources are visible.

### Journey E: Simulation

1. Owner asks for a decision simulation.
2. Hermes collects relevant Obsidian context.
3. Hermes writes simulation brief.
4. MiroFish runs multi-agent rehearsal.
5. Report writes to Obsidian.
6. Owner decides whether to create a decision note.

Success:

- simulation informs decisions;
- it does not execute actions.

### Journey F: Approval-Gated Action

1. User asks for a sensitive action.
2. Hermes classifies risk.
3. Hermes creates approval request.
4. Owner reviews in Brain UI or Feishu.
5. If approved, action enters controlled execution.
6. Audit log records request, decision, and result.

Success:

- no sensitive action happens silently;
- every step is auditable.

## 5. Commercial Interaction Rules

- Every surface must show capability state.
- Every long task must show progress.
- Every source-backed answer must show sources.
- Every memory promotion must be reviewable.
- Every high-risk action must require owner confirmation.
- Every deployment must have health output.
- Every connector must respect channel boundaries.

## 6. Packaging For Customers

Commercial packaging should provide:

- one-command local production deployment;
- domain server production deployment guide;
- default admin dashboard;
- setup wizard;
- connector status cards;
- backup and restore commands;
- upgrade command;
- support bundle export without secrets.

