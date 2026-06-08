# BaiLongma MOXI Overlay

Technical path source: https://github.com/LUTAO581314/hermes-

This directory records the MOXI changes that should be applied to a BaiLongma
checkout. It is intentionally an overlay, not a full copy of upstream source.

## Current Overlay Scope

- brand the public Brain UI as MOXI while preserving BaiLongma as the upstream
  runtime,
- add social connector settings for Feishu, WeChat, WeCom, and QQ,
- connect social surfaces to the Hermes runtime `/social/turn` and
  `/jobs/event` contract,
- keep voice input, browser TTS, image understanding, prepared stickers, and
  memory governance as explicit runtime capabilities,
- prevent high-risk company or money actions from running without owner
  confirmation.

## Patch Policy

- Never commit real `.env`, API keys, webhook secrets, cookies, QR-code session
  data, group ids, or private chat ids.
- Preserve upstream MIT license notices.
- Keep each patch focused: UI, connector, memory, performance, or deployment.
- Prefer small documented overlays over large source copies.
- Every phase that changes BaiLongma should add a Chinese report under
  `reports/`.

## Planned Patch Files

Patch files should be named by phase and purpose:

```text
phase-14-social-settings-ui.patch
phase-15-qq-connector.patch
phase-16-runtime-latency.patch
```

Until a patch file is exported, the server checkout remains the active working
copy and this folder documents the intended overlay boundary.

