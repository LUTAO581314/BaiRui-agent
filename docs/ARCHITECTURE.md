# Architecture

## 1. Design Principles

- Human-readable memory first.
- Agent execution must be logged.
- High-risk operations require explicit owner confirmation.
- Each tool should have a narrow role.
- Deployment should be reproducible from this repository.
- Secrets must stay outside committed files.

## 2. Layered Architecture

```text
Interaction Layer
  Feishu bot
  WeChat bridge
  BaiLongma UI
  CLI

Orchestration Layer
  Hermes
  job scheduler
  tool router
  MCP adapters

Knowledge Layer
  Obsidian vault
  SQLite metadata
  vector/Zep search if needed

Simulation Layer
  MiroFish
  multi-agent scenario reports

External Data Layer
  search engines
  crawl/extraction APIs
  OCR APIs
  vision APIs
  speech-to-text APIs
  video understanding APIs
  GitHub
  market data
  news
  server metrics
```

## 3. Data Flow

### 3.1 Command Flow

```text
Owner command
  -> Feishu / WeChat / CLI
  -> BaiLongma or Hermes command router
  -> Hermes task planner
  -> tools and data sources
  -> result summary
  -> Obsidian write-back
  -> notification to owner
```

### 3.2 Memory Flow

```text
Raw input
  -> temporary task context
  -> extracted facts and decisions
  -> Obsidian note
  -> optional vector index
  -> future retrieval
```

Obsidian remains the canonical readable record. Vector search is an index, not the source of truth.

### 3.3 API-First Multimodal Flow

```text
Image / PDF / video / web URL
  -> Hermes task router
  -> external API provider
  -> normalized text, entities, timestamps, and confidence notes
  -> Obsidian report
  -> optional private search index
  -> owner summary through Feishu or WeChat
```

The VPS should not run heavy local image or video models by default. It should coordinate API calls, validate outputs, keep logs, and write final artifacts.

### 3.4 Simulation Flow

```text
Obsidian notes
  -> simulation brief
  -> MiroFish multi-agent run
  -> simulation report
  -> decision note in Obsidian
  -> short owner summary
```

## 4. Suggested Obsidian Structure

```text
vault/
  00-Inbox/
  10-Owner/
    preferences.md
    goals.md
    standing-instructions.md
  20-Agents/
    hermes.md
    bailongma.md
    mirofish.md
    guardrails.md
  30-Projects/
  40-Research/
  50-Markets/
    watchlist.md
    daily-briefs/
    company-notes/
  60-Decisions/
  70-Reports/
    daily/
    weekly/
    simulations/
  80-Runbooks/
  90-Logs/
```

## 5. Service Layout on VPS

Recommended path:

```text
/opt/hermes-system/
  docker-compose.yml
  .env
  data/
  logs/
  obsidian-vault/
  backups/
```

The current lightweight VPS profile is enough for:

- Hermes orchestration.
- Feishu and callback adapters.
- Search/crawl API calls.
- OCR, image, speech, and video API routing.
- Lightweight local indexing.
- Obsidian vault write-back.
- Logs, queues, retries, and backups.

It is not intended for:

- Local large language model inference.
- Local video understanding models.
- Local GPU-heavy OCR or object detection.
- High-throughput crawling.

Recommended Linux users:

- `root` only for installation and emergency maintenance.
- `hermes` for service ownership and runtime files.

## 6. Networking

Recommended default:

- Do not expose raw agent ports publicly.
- Use a reverse proxy when a domain is available.
- Protect dashboards and callbacks with authentication.
- Restrict callback endpoints to messaging platform requirements.

## 7. Secrets

Never commit:

- Model API keys.
- Feishu app secrets.
- WeChat credentials.
- Market data API keys.
- Broker credentials.
- SSH private keys.

Use `.env` locally and keep only `.env.example` in Git.

## 8. Logging

Every important agent action should record:

- Timestamp.
- Trigger source.
- Task id.
- Tools used.
- Files written.
- External services called.
- Summary.
- Whether owner approval was required.

## 9. Backups

Back up:

- Obsidian vault.
- Hermes data directory.
- SQLite databases.
- Configuration templates.
- Logs needed for audit.

Do not back up plaintext secrets into shared locations.

## 10. Failure Modes

Plan for:

- Model API outage.
- Messaging callback outage.
- Bad or hallucinated research output.
- Unexpected tool execution.
- Financial data errors.
- Disk full.
- Agent loop runaway.
- Compromised token.

Each failure should degrade to notification and manual intervention rather than silent autonomous action.
