# Social And Runtime Performance Optimization Plan

Technical path source: https://github.com/LUTAO581314/hermes-

## 1. Problem

Social channels feel slow when the agent waits for the full model and tool loop
before saying anything. A 20-40 second final result can be acceptable for image
generation or source-backed research, but a 20-second silent gap feels broken
and unlike a real person.

The fix has two layers:

1. Surface layer: make the agent visibly present within 1-2 seconds.
2. Bottom layer: shorten the actual critical path and move slow work to async
   jobs.

## 2. Target Experience

| Scenario | First response | Final result |
| --- | --- | --- |
| Simple chat | direct answer within 5 seconds | same message |
| Complex question | "我想想哦，马上回你～" | concise answer after reasoning |
| Image reading | "我看一下这张图，等我一下哦～" | image analysis |
| Image generation | "等我拍一下，马上给你～" | generated image URL or upload |
| Search / public opinion | "我查一下，别急～" | source-backed result |
| Feishu company task | "我看一下上下文，马上处理～" | answer, draft, or confirmation card |

## 3. Surface Layer Tasks

### 3.1 Quick Acknowledgement

Add a channel-level quick acknowledgement before the heavy model path.

Rules:

- Only trigger for slow-looking work.
- Do not trigger for tiny confirmation messages.
- Use sender/channel cooldown to avoid spam.
- Store `quickAckSent` in the queued message metadata.
- The LLM/tool layer must know quick ack already happened.

### 3.2 Slow Tool Acknowledgement

If no channel quick acknowledgement happened, the tool loop can still send a
single progress message before a slow tool.

Rules:

- One progress acknowledgement per turn.
- It does not count as final delivery.
- It must not suppress the final result.
- Tool-specific wording should sound natural.

### 3.3 Social Tone Guard

On WeChat and Feishu:

- default to 1-3 short sentences,
- avoid headings and bullet lists,
- avoid "I am processing" narration after a quick acknowledgement,
- send final results plainly.

## 4. Bottom Layer Tasks

### 4.1 Latency Telemetry

Record these stages:

| Metric | Meaning |
| --- | --- |
| intake_ms | webhook or connector receive time |
| quick_ack_ms | time to first visible acknowledgement |
| context_ms | memory/context/tool-schema preparation |
| first_token_ms | time to first model text or tool name |
| tool_ms | tool runtime duration |
| final_send_ms | time to final user-visible result |
| total_ms | complete turn latency |

### 4.2 Route Classifier

Use a cheap rule-first classifier before building heavy context:

```text
message
  -> route type
  -> latency budget
  -> model slot
  -> tool set
  -> memory depth
```

Route types:

- casual_chat,
- quick_question,
- image_read,
- image_generate,
- search,
- public_opinion,
- company_task,
- memory_task,
- high_risk.

### 4.3 Context Budget

| Route | Memory depth | Tool schemas |
| --- | --- | --- |
| casual_chat | identity + recent chat | send only |
| quick_question | recent chat + critical memory | minimal |
| image_read | image tool + recent chat | vision tools |
| image_generate | image tool only | image generation |
| search | recent chat + source policy | search tools |
| company_task | Feishu identity + company policy | Feishu read tools |
| high_risk | policy + confirmation | no write tools |

### 4.4 Async Job Queue

Slow work should be a job with stable state:

```text
queued
  -> acknowledged
  -> running
  -> completed
  -> delivered
```

Failure state:

```text
queued
  -> acknowledged
  -> running
  -> failed
  -> failure_delivered
```

Job metadata:

- job id,
- channel,
- target id,
- route type,
- input preview,
- tool name,
- status,
- started at,
- completed at,
- result pointer,
- error message,
- owner confirmation requirement.

### 4.5 Interruption Policy

Follow-up messages should not automatically cancel slow jobs.

Rules:

- Ordinary follow-up messages add context.
- "不用了", "取消", or explicit cancellation stops the job.
- Image reading and image generation jobs are locked until completed or
  cancelled.
- Company writes require confirmation even if the job completes successfully.

## 5. Model Routing

| Slot | Use | Latency goal |
| --- | --- | --- |
| fast | quick ack draft, classification, dedupe | sub-second to low seconds |
| summary | digest, report draft, source grouping | medium |
| reasoning | final judgment, planning, sensitive company tasks | slower but higher quality |
| vision | image understanding | provider-dependent |
| image_generation | original images and stickers | async |

## 6. Minimal Runtime Support

The repository runtime exposes:

- `/health` with performance profile,
- `/performance` with latency budgets and model slots,
- environment variables for latency targets:
  - `HERMES_SOCIAL_QUICK_ACK_DELAY_MS`,
  - `HERMES_SOCIAL_FAST_REPLY_TARGET_MS`,
  - `HERMES_SLOW_TASK_THRESHOLD_MS`,
  - `HERMES_ASYNC_TASK_TIMEOUT_SECONDS`,
  - `HERMES_LATENCY_TELEMETRY_ENABLED`.

This is intentionally safe: performance endpoints expose no API keys, secrets,
server addresses, chat logs, or private runtime names.

## 7. Implementation Order

1. Surface quick ack and social tone.
2. Performance profile and safe health endpoints.
3. Latency logs around connector, context, model, tool, and send.
4. Intent router and context slimming.
5. Async job queue for image/search/company work.
6. Model slot routing.
7. Cost and cache tracking.

## 8. Acceptance Criteria

- Complex social messages receive visible feedback in 1-2 seconds.
- Simple social replies target <= 5 seconds.
- Image generation and image reading can take longer but never stay silent.
- Progress acknowledgements do not suppress final answers.
- `/performance` returns safe latency budgets.
- No secrets are exposed in performance, health, docs, tests, or logs.
