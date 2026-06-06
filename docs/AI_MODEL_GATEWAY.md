# AI Model Gateway

## 1. Decision

Hermes should use an OpenAI-compatible multi-model gateway for model calls.

The current owner-provided gateway is:

```text
Provider: supermoxi
Base URL: https://api.supermoxi.cn
```

The API key must stay only in the server-side `.env` file and must never be committed.

## 2. Configuration

```env
HERMES_AI_PROVIDER=supermoxi
HERMES_AI_BASE_URL=https://api.supermoxi.cn
HERMES_AI_API_KEY=
HERMES_AI_DEFAULT_MODEL=
HERMES_AI_FAST_MODEL=
HERMES_AI_REASONING_MODEL=
HERMES_AI_VISION_MODEL=
HERMES_AI_TIMEOUT_SECONDS=60
```

Model slots:

- `HERMES_AI_DEFAULT_MODEL`: default general chat and summarization model.
- `HERMES_AI_FAST_MODEL`: cheap/fast model for classification, routing, extraction, and simple drafts.
- `HERMES_AI_REASONING_MODEL`: stronger model for planning, code reasoning, research synthesis, and risk review.
- `HERMES_AI_VISION_MODEL`: multimodal model for image/OCR/screenshot tasks if supported by the gateway.

## 3. Runtime Exposure

The `/health` endpoint may report:

- provider name,
- whether base URL is configured,
- whether API key exists,
- configured model names.

It must not report the API key.

## 4. Current Status

The local minimal Hermes runtime still exposes configuration state only.

BaiLongma is already configured on the VPS to call the custom GPT-5.5 gateway for chat and image understanding. The real API key stays only in server-side configuration.

Next Hermes-side model work should be added through a narrow adapter with:

- no key exposure in logs or health output,
- timeout and retry limits,
- per-capability model slots,
- cost/rate tracking,
- tests for failure and redaction behavior.
