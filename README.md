# Hermes Personal Agent System

This repository is the planning and deployment home for a personal agent system built around Hermes, Obsidian, BaiLongma, MiroFish, and communication adapters.

The goal is not to install one chatbot. The goal is to build a layered personal AI operating system:

- Obsidian stores durable human-readable memory.
- Hermes runs backend automation, research, tools, and scheduled jobs.
- BaiLongma provides a Chinese-facing interaction layer for WeChat, Feishu, voice, and Brain UI style workflows.
- MiroFish acts as a scenario simulation and report lab.
- Feishu and WeChat deliver summaries, alerts, and human confirmation loops.
- Financial workflows stay research-first and require explicit human approval before any real trading action.
- Search, image recognition, and video understanding are API-first integrations; the lightweight VPS runs orchestration, not heavy local models.

## Current Status

This repository currently contains the full architecture and rollout plan. Runtime deployment files will be added after the model provider, domain, communication channels, and security boundaries are confirmed.

## Documents

- [Master Plan](docs/MASTER_PLAN.md)
- [Architecture](docs/ARCHITECTURE.md)
- [API Integrations](docs/API_INTEGRATIONS.md)
- [Roadmap](docs/ROADMAP.md)
- [Risk and Guardrails](docs/RISK_AND_GUARDRAILS.md)

## Recommended First Milestone

Build a minimal but useful system first:

1. Deploy Hermes on the VPS.
2. Create an Obsidian vault structure for durable memory.
3. Add a Feishu bot for daily summaries and manual commands.
4. Add a research-only market watch workflow.
5. Write every important output back to Obsidian.
6. Add external APIs for search, OCR, image understanding, speech transcription, and video understanding.

WeChat, BaiLongma, MiroFish, and trading execution should be added only after the memory and research loop is stable.

## Guiding Principle

Memory must remain portable and readable. Automation must remain reversible and auditable. Any high-risk action must stop at a human confirmation boundary.
