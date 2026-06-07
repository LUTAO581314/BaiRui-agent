# MOXI White-Label Architecture

## Layered Design

```text
User surfaces
  -> Chat UI / WeChat-style personal channel / future company channel

Interaction layer
  -> message normalization
  -> channel policy
  -> visible panels: memory graph, hot-list panel, voice panel

Orchestration core
  -> task routing
  -> model routing
  -> tool calling
  -> scheduled jobs
  -> guardrails

External runtimes and APIs
  -> search and trend intelligence
  -> public-opinion crawling
  -> image/OCR model API
  -> voice ASR/TTS providers
  -> company platform APIs

Memory and reporting
  -> working memory
  -> reviewed durable notes
  -> phase reports
  -> rebuildable indexes
```

## Design Principles

- Keep the lightweight VPS as an orchestrator, not a heavy model host.
- Use APIs or external runtimes for expensive capabilities.
- Keep public UI branding separate from private runtime names.
- Keep all source-backed intelligence auditable.
- Separate working memory from durable memory.
- Require human approval for high-risk actions.

## Suggested Module Boundaries

| Module | Responsibility |
| --- | --- |
| Interaction surface | Chat, voice input, visual panels, personal channel UX |
| Orchestrator | Routing, jobs, tools, policy, retries, model selection |
| Memory governor | Admission rules, review, consolidation, durable write-back |
| Trend intelligence | Search, hot-list ingestion, public-opinion reports |
| Media adapter | Image/OCR, ASR, TTS, future video |
| Company adapter | Documents, tasks, approvals, reminders, summaries |
| Safety layer | Permissions, audit logs, approval gates, secret handling |

## External AI Review Questions

When reviewing this architecture, focus on:

- whether the module boundaries are clean,
- whether the first milestone is too broad,
- whether memory governance is strong enough,
- whether public-opinion workflows are source-backed,
- whether model routing is cost-effective,
- whether safety gates are sufficient for company and financial workflows.

