# Search Runtime Strategy

## 1. Decision

Hermes does not require a hosted search provider key for the current plan.

Search and trend intelligence should be connected through external projects:

- Primary: TrendRadar.
- Optional self-hosted search supplement: SearXNG.
- No hosted search provider is required in the current plan.

This keeps the lightweight VPS in orchestration mode while still allowing search, hot-news tracking, RSS, trend monitoring, and recurring intelligence reports.

## 2. Configuration

Use project-runtime settings:

```env
HERMES_SEARCH_MODE=external_project
HERMES_SEARCH_PROJECT=trendradar
HERMES_TRENDRADAR_BASE_URL=
HERMES_TRENDRADAR_MCP_COMMAND=
HERMES_SEARXNG_BASE_URL=
```

The empty values mean the runtime foundation is ready, but the external search project is not yet attached.

## 3. TrendRadar Role

TrendRadar should provide:

- Hot news and trend radar.
- RSS aggregation.
- Recurring market, AI, competitor, and opportunity briefings.
- MCP, HTTP, CLI, or report-file integration when available.
- Feishu and Obsidian report inputs after the adapter is built.

License boundary:

- TrendRadar is GPL-3.0.
- Keep it as an isolated external runtime.
- Do not copy TrendRadar source code, prompt bundles, or implementation internals into this repository.

## 4. SearXNG Role

SearXNG can be added later if Hermes needs a self-hosted metasearch project.

Use it as:

- A local/private search endpoint.
- A supplement to TrendRadar, not a replacement for trend intelligence.
- A project runtime with URL configuration, not an API key dependency.

## 5. Adapter Contract

Hermes should normalize search-project output into the same shape used by other intelligence adapters:

```json
{
  "provider": "trendradar",
  "capability": "search|trend|rss|news",
  "input_ref": "query-or-topic",
  "summary": "short result",
  "structured_data": {},
  "sources": [],
  "confidence": "low|medium|high",
  "created_at": "ISO-8601 timestamp"
}
```

## 6. Phase Placement

Phase 4 should build the first external search-project adapter.

Recommended order:

1. Configure TrendRadar as an isolated runtime.
2. Add a Hermes adapter that can read TrendRadar output through MCP, HTTP, CLI, or report files.
3. Write one source-backed trend/search report to Obsidian.
4. Send a short owner-facing summary through Feishu after Feishu is ready.
5. Add SearXNG only if plain metasearch is still needed.

## 7. Current Status

Phase 1 only declares the configuration shape.

The Hermes runtime can report that search mode is `external_project`, but it does not call TrendRadar or SearXNG yet.
