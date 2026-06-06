# Hermes Personal Agent System

This repository is the planning and deployment home for a personal and company agent system built around Hermes, Obsidian, BaiLongma, MiroFish, Feishu, WeChat, and API-first intelligence adapters.

The goal is not to install one chatbot. The goal is to build a layered AI operating system for both personal work and company management:

- Obsidian stores durable human-readable memory.
- Hermes runs backend automation, research, tools, and scheduled jobs.
- Feishu is the primary company management console.
- WeChat is the personal companionship and lightweight reminder channel.
- BaiLongma provides a Chinese-facing interaction/persona layer across WeChat, Feishu, voice, and Brain UI style workflows.
- MiroFish acts as a scenario simulation and report lab.
- Feishu and WeChat deliver summaries, alerts, and human confirmation loops.
- Financial workflows stay research-first and require explicit human approval before any real trading action.
- Search, image recognition, and video understanding are API-first integrations; the lightweight VPS runs orchestration, not heavy local models.

## Current Status

This repository currently contains the full architecture and rollout plan. Runtime deployment files will be added after the model provider, domain, communication channels, and security boundaries are confirmed.

## Documents

- [Master Plan](docs/MASTER_PLAN.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Optimized Architecture](docs/OPTIMIZED_ARCHITECTURE.md)
- [API Integrations](docs/API_INTEGRATIONS.md)
- [Roadmap](docs/ROADMAP.md)
- [Risk and Guardrails](docs/RISK_AND_GUARDRAILS.md)
- [Chinese Report Policy](docs/CHINESE_REPORT_POLICY.md)
- [Current Chinese Phase Report](reports/phase-00-architecture-plan.zh-CN.md)

## Recommended First Milestone

Build a minimal but useful system first:

1. Deploy Hermes on the VPS.
2. Create an Obsidian vault structure for durable memory.
3. Add a Feishu company-management bot for tasks, reports, project tracking, and owner approvals.
4. Create company tables for projects, customers, sales pipeline, receivables, risks, and employee reports.
5. Add a research-only market watch workflow.
6. Write every important output back to Obsidian.
7. Add external APIs for search, OCR, image understanding, speech transcription, and video understanding.

WeChat companionship, BaiLongma persona features, MiroFish simulations, and trading execution should be added only after the company-management and memory loop is stable.

## Guiding Principle

Memory must remain portable and readable. Automation must remain reversible and auditable. Any high-risk action must stop at a human confirmation boundary.

## Reporting Rule

Every implementation phase must produce a Chinese report for the owner. Research notes and source materials may remain in English, but phase summaries, delivery status, decisions, risks, and next actions must be written in Chinese.
