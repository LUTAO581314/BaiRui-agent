# MOXI Memory Governance

## Goal

MOXI should remember fewer, better, relationship-rich facts instead of storing
every message, log, test output, and temporary mood as permanent memory.

## Memory Layers

```text
conversation and runtime events
  -> working memory
  -> review gate
  -> durable human-readable notes
  -> rebuildable indexes
```

## Rules

- Time is metadata, not the main structure.
- Durable memory should be associative, source-backed, and owner-correctable.
- Test output, greetings, health checks, QR login state, and temporary role
  experiments should not become durable memory.
- Stable preferences, architecture decisions, repeated patterns, explicit owner
  instructions, and project facts may become durable memory after review.

## Dream Consolidation

Dream consolidation is a read-only review pass by default.

It should:

- inspect recent working memories,
- find duplicates and noise,
- suggest merges,
- suggest forgotten items,
- suggest durable note candidates,
- require owner approval before deletion or promotion.

## Public-Opinion Memory Boundary

Hot-list items should remain working context unless:

- the owner explicitly asks to track a topic,
- the item becomes part of a report,
- it affects a project, client, competitor, risk, or strategy,
- it is tied to a durable decision.

