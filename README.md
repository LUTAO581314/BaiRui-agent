# bairui

This repository is the source-owned engineering framework for the bairui
industrial agent product.

Customer-facing product surfaces must expose only the `bairui` brand. Historical
project names, upstream runtime names, and third-party repository names are
internal engineering details and must not appear in the customer frontend,
activation flow, setup copy, or public product contract.

## Current Repository State

This repository contains:

- current product and architecture documents under `docs/`;
- environment templates and deployment skeleton files;
- `src/` as the rebuilt runtime source location;
- `tests/` as the rebuilt test suite location.

This repository intentionally does not contain:

- old runtime implementation files;
- old tests tied to removed implementation details;
- external project patches;
- copied frontend prototypes;
- historical phase report noise;
- runtime data, logs, secrets, sessions, QR state, or generated media.

## Product Direction

bairui provides one controlled backend, one primary user experience, governed
long-term memory, company workflow automation, document intelligence, voice
input, search, reports, and owner-approved execution.

The commercialization requirement is a quality bar, not a command to build
everything from a blank file. The product should prioritize mature, working
source code as substrate whenever the license and architecture fit.

The preferred path is:

- use mature open-source runtime code directly when it is useful;
- keep original licenses, notices, source names, and attribution in internal
  engineering boundaries;
- put third-party runtime code under `vendor/runtimes/` or another explicit
  boundary;
- build bairui product behavior, configuration, deployment, license,
  readiness, and frontend contracts around those runtimes;
- avoid AI-only blank-slate rewrites for complex agent internals unless a
  small owned component is clearly safer than integrating an existing one.

The frontend should use the owner-approved open-source UI base only for
interaction patterns, component density, layout rhythm, and visual inspiration.
All public copy, product name, logo text, route labels, activation steps, empty
states, and reports must be changed to `bairui`.

Internal frontend source reference:

- Repository: `https://github.com/xiaoyuanda666-ship-it/BaiLongma`
- License: MIT
- Scope: frontend interaction model, component behavior, activation experience,
  voice panel patterns, media panels, realtime UI events, and workbench layout.
- Boundary: do not expose the upstream project name, package name, logo, or
  route labels to customers; backend integration is supplemental only.

## Documentation Map

- [Product Blueprint](docs/00-product-blueprint.md)
- [System Architecture](docs/01-system-architecture.md)
- [Server Rebuild And Deployment](docs/02-server-rebuild-and-deployment.md)
- [PostgreSQL Data Architecture](docs/03-postgresql-data-architecture.md)
- [Backend Runtime](docs/04-hermes-backend-runtime.md)
- [Memory And Notes](docs/05-memory-obsidian-everos.md)
- [Intelligence: Models, Search, And Crawling](docs/06-intelligence-model-search.md)
- [Simulation](docs/07-simulation-mirofish.md)
- [Connectors And Channels](docs/08-connectors-and-channels.md)
- [Frontend: bairui UI](docs/09-frontend-moxi-brain-ui.md)
- [Security, Compliance, And Operations](docs/10-security-compliance-ops.md)
- [Commercial Productization Roadmap](docs/11-commercial-roadmap.md)
- [One-Click Deployment To Usable Stage](docs/12-one-click-deployment.md)
- [Source Rebuild Technical Path](docs/13-source-rebuild-technical-path.md)
- [Commercial Interaction Model](docs/14-commercial-interaction-model.md)
- [GitHub Repository Cleanup Policy](docs/15-github-repository-cleanup.md)
- [Commercial Delivery Development Plan](docs/16-commercial-delivery-development-plan.md)
- [Three-Pillar Commercial Project Plan](docs/17-three-pillar-commercial-project-plan.md)
- [Vendor Runtime Integration](docs/18-vendor-runtime-integration.md)
- [Brand And Trademark Fields](docs/19-brand-and-trademark-fields.md)
- [bairui Frontend Source UI Integration](docs/20-bairui-frontend-source-ui-integration.md)
- [Backend Contract Freeze For Frontend](docs/21-backend-contract-freeze-for-frontend.md)
- [bairui Frontend Design And Source UI Modification](docs/22-bairui-frontend-design-and-source-ui-modification.md)
- [bairui Avatar Runtime Backend Integration](docs/23-bairui-avatar-runtime-backend-integration.md)
- [bairui Frontend Screens And UI Design](docs/24-bairui-frontend-screens-and-ui-design.md)
- [Product Demo Acceptance](docs/25-product-demo-acceptance.md)
- [Activation 3D Interaction Prompt](docs/26-bairui-activation-3d-interaction-prompt.md)
- [Commercial Trial Delivery Quickstart](docs/27-commercial-trial-delivery-quickstart.md)
- [Third-Party Attribution Inventory](docs/28-third-party-attribution-inventory.md)
- [Commercial Trial Handoff Pack](docs/29-commercial-trial-handoff-pack.md)
- [Server Deployment Acceptance Report](docs/30-server-deployment-acceptance-report.md)
- [PostgreSQL Production Verification](docs/31-postgresql-production-verification.md)
- [Commercial Go/No-Go Report](docs/32-commercial-go-no-go-report.md)

## CLI Entry Point

```bash
python -m src.hermes --help
python -m src.hermes status
python -m src.hermes capabilities
python -m src.hermes frontend-contract
python -m src.hermes events
python -m src.hermes channels status
python -m src.hermes channels targets
python -m src.hermes channels diagnostics
python -m src.hermes channels approvals --pending
python -m src.hermes channels plan-send --target-id owner_review --text "Review this update"
python -m src.hermes channels review-approval --request-id <request_id> --decision approve
python -m src.hermes codegraph status
python -m src.hermes codegraph register --path . --name bairui-source
python -m src.hermes codegraph scan --repo-id <repo_id>
python -m src.hermes codegraph query --query "build_frontend_contract"
python -m src.hermes codegraph impact --path src/hermes/server.py
python -m src.hermes memory status
python -m src.hermes memory search --query "owner preferences"
python -m src.hermes voice asr status
python -m src.hermes document parse status
python -m src.hermes document parse ingest-plan --input-path ./sample.pdf --title "Sample"
python -m src.hermes document parse session-list --limit 50
python -m src.hermes document parse session-summary --ingest-id <ingest_id>
python -m src.hermes document parse workbench-next --ingest-id <ingest_id>
python -m src.hermes document parse workbench-run-until-blocked --ingest-id <ingest_id>
python -m src.hermes runtime-readiness
python -m src.hermes admin-session
python -m src.hermes diagnostics
python -m src.hermes metrics
python -m src.hermes errors
python -m src.hermes backup status
python -m src.hermes backup plan
python -m src.hermes backup restore-plan --backup-path ./data/backups/postgres/example.dump
python -m src.hermes demo seed
python -m src.hermes demo flow
python -m src.hermes serve
```

## Quickstart: Local Product Demo

From a clean checkout:

```bash
python -m pip install -r requirements.txt
python -m src.hermes demo flow
python -m src.hermes serve
```

Then open:

```text
http://127.0.0.1:8787/console
```

For Windows PowerShell verification:

```powershell
.\scripts\smoke-test.ps1
.\scripts\smoke-test.ps1 -FullAcceptance
.\scripts\product-acceptance.ps1
.\scripts\check-server-prereqs.ps1
.\scripts\verify-server-deployment.ps1
.\scripts\verify-postgres-production.ps1
.\scripts\commercial-go-no-go.ps1
.\scripts\config-doctor.ps1
.\scripts\check-public-brand.ps1
```

The smoke test runs the product closure demo flow in a temporary data directory.
It verifies Command -> Report, Memory Review, Channels approval, CodeGraph, and
the safety gates that prevent external sends and automatic long-term memory
writes.

Use `-FullAcceptance` when preparing a demo or release candidate. The default
smoke command remains fast for CI and local sanity checks.

The product acceptance script expands the same real backend flow into seven
demo scenarios: research task, document knowledge base, customer draft
approval, code understanding, runtime diagnostics, safe configuration
diagnostics, and the local owner admin gate. It can also write a JSON report
with `-OutputPath artifacts\product-acceptance.json`.

Use `scripts/config-doctor.ps1` when you need an operator-safe configuration
diagnostic from the CLI without opening the browser.

Use `scripts/check-server-prereqs.ps1` before a local, LAN, or domain
deployment. It checks deployment assets, Git, Python, Docker / Compose,
environment file presence, port availability, DNS when needed, disk space, and
runtime path writability, then writes `artifacts\server-prereq-check.json`.

Use `scripts/verify-server-deployment.ps1` after the deployment is running. It
verifies the target `/health`, `/ready`, `/runtime/readiness`,
`/frontend/contract`, `/console`, `/demo/flow`, `/admin/session`,
`/config/status`, and optional PostgreSQL readiness evidence, then writes
`artifacts\server-deployment-verification.json`.

Use `scripts/run-server-trial-acceptance.ps1` on a prepared target server when
you want the full Step 2 evidence chain in one command. It runs preflight,
usable deployment unless skipped, post-deployment verification, PostgreSQL
proof when required, commercial Go/No-Go, and the handoff bundle export, then
writes `artifacts\server-trial-acceptance.json`.
It also writes `artifacts\server-trial-failure-summary.md` so failed, blocked,
or skipped server steps can be repaired without digging through raw JSON.
It writes `artifacts\server-trial-execution-plan.md` with the exact target
server command sequence, required evidence paths, and current skip flags.
On Linux servers, use `scripts/run-server-trial-acceptance.sh` with environment
variables such as `MODE=domain`, `DOMAIN=bairui.example.com`,
`BASE_URL=https://bairui.example.com`, `REQUIRE_POSTGRES=1`, and
`INCLUDE_DOCS=1`.

Use `scripts/verify-postgres-production.ps1` before and during production
database validation. Dry-run mode checks migration schema coverage, backup and
restore guardrails, Settings visibility, and secret redaction. On a target
server, run it with `-RequireDatabase -RunMigration` to prove the configured
PostgreSQL database is ready. It writes
`artifacts\postgres-production-verification.json` and
`artifacts\postgres-production-failure-summary.md`.

Use `scripts/commercial-go-no-go.ps1` as the final commercial trial gate. Local
mode checks repository hygiene, public brand, deployment assets, product
acceptance, frontend commercial closure hooks, and handoff docs. Add
`-RequireServerEvidence -RequirePostgresEvidence` when target-server and
database evidence are present. It writes `artifacts\commercial-go-no-go.json`.

Use `scripts/export-commercial-handoff-bundle.ps1` after collecting server and
PostgreSQL evidence. It regenerates local product acceptance and Go/No-Go
reports by default, copies only operator-safe JSON reports, writes
`artifacts\commercial-handoff-bundle\manifest.json`, and marks missing server
or PostgreSQL evidence as blocked instead of pretending the trial is ready.

To seed only static walkthrough records before opening the console:

```bash
python -m src.hermes demo seed
python -m src.hermes serve
```

The demo seed creates one job, one draft report, one memory candidate, and one
channel approval draft. It does not send external messages or write long-term
memory. The Dashboard also has a `Run Demo Flow` button that calls the real
`POST /demo/flow` backend contract and shows checkpoint evidence.

## Multi-Agent Command Boundary

The command workspace has a governed multi-agent backend contract:

- `GET /agents`
- `POST /agents/session`
- `POST /agents/session/{session_id}/round`
- `GET /agents/session/{session_id}/events`
- `POST /agents/session/{session_id}/promote`

Agents expose role, model, permission, and readiness state. Missing model
configuration disables model-backed agents without hiding approval-required or
operator-safe states. Memory and channel agents can propose review items, but
external sends and memory writes remain owner-reviewed.

## Frontend Contract

- `GET /frontend/contract`
- `python -m src.hermes frontend-contract`
- `GET /console`

The contract lists stable bairui product surfaces, including activation,
dashboard, command, documents, memory review, reports, CodeGraph, and runtime settings.
It also includes the complete activation steps, renderable action forms, status
values, and premium sci-fi UI design tokens.

## CodeGraph Boundary

CodeGraph is a local source-structure index for repositories, files, symbols,
imports, and impact analysis. It helps AI understand code layout without mixing
source code into long-term memory.

- CodeGraph stores code structure under `BAIRUI_CODEGRAPH_ROOT`.
- Long-term memory and report notes remain separate.
- CodeGraph does not auto-promote facts into memory.
- CodeGraph actions are audited and read source structure only.

## Deployment

Local usable deployment remains:

```bash
bash scripts/deploy-usable.sh
```

Windows usable deployment:

```powershell
.\scripts\deploy-usable.ps1 -Mode local
```

Both scripts print the `/console` URL and write `data/readiness.json`, including
health, readiness, runtime readiness, capabilities, and Demo Flow evidence.

Before deployment on a target machine, capture a preflight report:

```powershell
.\scripts\check-server-prereqs.ps1 -Mode local
```

After the target server is running, capture a deployment verification report:

```powershell
.\scripts\verify-server-deployment.ps1 -BaseUrl http://127.0.0.1:8787 -RequireReady
```

Commercial Linux service assets live under `infra/hermes`:

```bash
sh infra/hermes/scripts/deploy-hermes.sh
```

Copy `infra/hermes/env.example` to a protected server path and set real values
before production service install.
