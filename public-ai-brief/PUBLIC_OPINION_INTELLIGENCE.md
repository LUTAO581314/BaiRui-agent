# MOXI Public-Opinion Intelligence

## Goal

MOXI should let the owner see what has already been collected and then ask for
deeper analysis when needed.

The hot-list panel is not a decorative dashboard. It is the first visual surface
for already-collected public trend data.

## Workflow

```text
platform hot-list collection
  -> MOXI hot-list panel
  -> user selects or asks about a topic
  -> external trend/search runtime expands sources
  -> model tiers classify, summarize, and score risk
  -> report written to durable notes or sent to the owner
```

## First Visual Surface

The panel should show:

- platform,
- rank,
- title,
- heat or label,
- trend direction if available,
- update time,
- source status.
- clickable source or search links.
- a bottom event feed for already-collected trend/news/RSS items.

Initial platform categories:

- short-video hot list,
- lifestyle/community hot list,
- social hot topics,
- microblog hot search.
- external trend/news/RSS feed cards.

## Deeper Analysis

After a topic is selected, deeper analysis should include:

- source expansion,
- duplicate merging,
- topic clustering,
- sentiment and risk labels,
- timeline,
- stakeholder impact,
- business opportunity or threat,
- recommended follow-up actions,
- sources and freshness notes.

## Model Split

- `5.4 mini`: fast labels, deduplication, sentiment tags, risk tags.
- `5.4`: summary, topic clustering, daily or weekly digest draft.
- `5.5`: final judgment, high-stakes strategy, owner-facing final report.

## Guardrails

- Do not treat hot-list data as verified fact by itself.
- Always preserve source and freshness metadata.
- Do not write noisy hot-list items into durable memory automatically.
- Only promote durable notes after review or clear owner instruction.
