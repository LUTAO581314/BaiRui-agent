# MOXI Model Routing

## Goal

Use multiple model tiers so the system is affordable, fast, and reliable.

The model gateway should expose slots instead of hard-coding one model
everywhere.

## Recommended Slots

| Slot | Example Model Tier | Use |
| --- | --- | --- |
| fast | 5.4 mini | classification, routing, deduplication, labels, short extraction |
| summary | 5.4 | hotspot summaries, public-opinion digests, daily/weekly report drafts, medium-depth synthesis |
| reasoning | 5.5 | final judgment, strategy, complex planning, sensitive decisions, owner-facing final reports |
| vision | vision-capable model | image understanding, OCR, screenshots, charts |

## Public-Opinion Flow

```text
crawled hot-list items
  -> 5.4 mini for fast labels and deduplication
  -> 5.4 for summary and trend digestion
  -> 5.5 for final risk judgment or strategy report
```

## Routing Rules

- Use `5.4 mini` for high-volume low-risk batch analysis.
- Use `5.4` when the output needs readable summaries, topic grouping, and
  medium-context synthesis.
- Use `5.5` only when the result affects strategy, safety, money, company
  operations, or final owner-facing decisions.
- Do not use a model as a crawler. Crawling and source collection are tool or
  runtime responsibilities.
- Track cost, latency, source freshness, and confidence for every intelligence
  workflow.

## Safety

The model layer must not expose API keys in logs, health endpoints, reports, or
client-side code.

