# Hermes Frontend Adapter Plan

Technical path source: https://github.com/LUTAO581314/hermes-

## Core Decision

Hermes has its own agent logic. MOXI should integrate with it instead of
rewriting that logic in the frontend.

The frontend adapter owns:

- channel UI,
- capability display,
- settings UX,
- quick acknowledgement state,
- worker progress state,
- permission hints,
- human confirmation surfaces.

Hermes owns:

- native agent reasoning flow,
- internal tool orchestration,
- long-running task execution,
- memory and skill logic that already belongs to Hermes.

MOXI runtime owns:

- secret-safe capability matrix,
- social-turn planning,
- job lifecycle events,
- latency telemetry,
- channel policy,
- owner confirmation boundaries,
- public technical path and reproducible overlay docs.

## Frontend Architecture

```text
BaiLongma / Brain UI
  -> settings panel
  -> capability matrix panel
  -> chat / voice / image / sticker controls
  -> Hermes frontend adapter
       -> GET /capabilities
       -> POST /social/turn
       -> POST /jobs/event
       -> GET /latency
       -> upstream Hermes native actions
```

## UI Improvements

### Settings

- Split social settings into channel cards.
- Add QQ as a first-class social channel.
- Add runtime connector settings.
- Show status chips from `/capabilities`.
- Keep save/test/copy actions near each channel.

### Chat

- Send a natural quick acknowledgement for slow tasks.
- Show "thinking / looking / generating" state before final result.
- Do not cancel an active image/search/company job when the user sends a
  follow-up; append it as context unless the user explicitly cancels.

### Company Plane

- Feishu company management must show identity and group context.
- Company writes require owner confirmation.
- The same companion persona can speak warmly, but permissions must remain
  separated by channel and action type.

### Personal Plane

- WeChat, QQ, and web chat can use the companion persona.
- Personal channels cannot approve company, money, legal, HR, or destructive
  actions.

## Implementation Order

1. Add `/capabilities` to the MOXI runtime.
2. Render capability cards in the public website and later Brain UI.
3. Export the first BaiLongma patch for settings UI and QQ entry.
4. Add runtime connector test buttons.
5. Add progress events to chat UI.
6. Add company/persona permission badges.
7. Add GitHub Pages deployment for the public technical path.

