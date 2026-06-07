# Core Hermes and BaiLongma MVP Runbook

## 1. Locked Scope

Current core scope:

- Hermes orchestration.
- BaiLongma Brain UI and Chinese interaction layer.
- GPT-5.5 through the configured custom OpenAI-compatible gateway.
- TrendRadar as the external search and trend runtime.
- Governed, human-like memory.
- Tool calling.
- Image understanding and OCR.
- Voice input through local Whisper.

Frozen for this phase:

- Video understanding.
- AI video generation.
- Voice cloning.
- Autonomous trading.
- Feishu company management.

The goal is not to enable every possible feature. The goal is to prove a clean loop:

```text
owner message
  -> BaiLongma or Hermes
  -> governed memory context
  -> selected tools
  -> model response
  -> useful result
  -> Obsidian inbox or phase report
  -> memory dream consolidation
  -> reviewed cleanup
```

## 2. Current Runtime Map

| Component | Current Role | Status |
| --- | --- | --- |
| Hermes | Backend orchestrator, MCP and tool runner | Installed on the VPS |
| BaiLongma runtime / MOXI UI | Brain UI, Chinese interaction, WeChat companion bridge | Running behind protected `bairui.chat`; visible brand and agent profile name are `MOXI` |
| GPT-5.5 gateway | Main model and vision-capable model path | Configured in BaiLongma |
| TrendRadar | External search, RSS, trend and news runtime | Enabled through Hermes MCP; latest local output is also surfaced in the MOXI hotspot feed |
| MOXI hotspot panel | Visual hot-list and public-opinion inspection surface | Visible hotspot button opens `/hotspots` data from Douyin, Xiaohongshu, WeChat hot topics, Weibo, and TrendRadar feed cards |
| Local Whisper | Transitional ASR for voice input | Installed in a dedicated venv and verified through `/voice/cloud` |
| Browser speech output | Temporary web voice output | Current Brain UI speaking path; provider TTS is bypassed in the web dialogue loop |
| Image tool | Screenshot/image/OCR analysis | Exposed as `analyze_image` |
| Feishu chat callback | Official Feishu bot message ingress/egress | Webhook challenge, tenant token, event idempotency, fast ACK, and group-reply routing are verified; company-management workflows remain gated |
| Video tool | Not part of the current phase | Hidden from routing/schema |
| Obsidian | Durable source of truth | Governed write-back workflow documented |

## 3. What It Can Do Now

The current core can support:

- Chinese natural chat through BaiLongma Brain UI.
- MOXI-branded Brain UI at `https://bairui.chat/brain-ui.html`.
- Owner personal chat through the restored WeChat ClawBot state, if the saved login remains valid.
- Model calls through the custom GPT-5.5 gateway.
- Tool routing from Hermes and BaiLongma.
- Trend and search intelligence through Hermes + TrendRadar.
- Clickable hotspot/public-opinion panel showing already-collected hot-list data and TrendRadar news/RSS feed cards.
- Image recognition and OCR through `analyze_image`.
- Voice input transcription through local Whisper.
- Temporary web voice output through browser SpeechSynthesis without cloud TTS credentials.
- Brain UI now separates voice dictation from realtime voice conversation: the microphone button only controls listening, while the adjacent dialogue button enables auto-send plus spoken replies.
- Feishu bot chat callback through `https://bairui.chat/social/feishu/webhook`, once the Feishu app is subscribed to the correct message event.
- Short-term BaiLongma working memory with a governed promotion path.

Memory rule:

```text
BaiLongma memory = working memory
Obsidian = durable memory
reports = phase facts and delivery record
indexes = rebuildable lookup helpers
```

## 4. What It Must Not Do Yet

Do not treat these as ready:

- Real video understanding.
- Provider-grade cloud TTS; the current phase intentionally uses browser SpeechSynthesis only.
- Voice cloning.
- Feishu company operations.
- Broker or trading execution.
- Unreviewed permanent memory writes.
- WeChat-based money, HR, legal, company approval, or trading actions.

## 5. Tool Calling Acceptance Gate

Each tool capability must pass three checks before it is treated as usable:

| Capability | Required Check | Pass Criteria |
| --- | --- | --- |
| Hermes MCP | `hermes mcp list` | TrendRadar appears enabled |
| Brain UI | `/health` and `/status` | Service is running and memory count is visible |
| Model gateway | BaiLongma settings/status | Provider is `custom`, model is the intended model |
| Image | `analyze_image` smoke test, Brain UI image attachment test, and WeChat image retest | A test image can be described or OCR'd correctly; Brain UI accepts pasted/dragged/selected images; WeChat ClawBot saves inbound images and routes them to `analyze_image` |
| Voice | `/voice/cloud` transcript smoke | Local Whisper returns `asr_status`, `config_ok`, and a real transcript through BaiLongma |
| Memory | pre/post memory count | Setup tests do not create noisy durable memories |
| Search | TrendRadar MCP call or report | Output contains sources or clear uncertainty |
| Hotspot panel links | `/hotspots` and Brain UI resources | Platform titles and TrendRadar feed cards expose source or search links |
| Feishu chat | Public callback, tenant-token, idempotency, and route checks | `/social/feishu/webhook` is not behind Basic Auth, challenge returns 200, App ID/Secret can obtain a tenant token, duplicate events are ignored, and group replies use `chat_id` |
| Runtime graph | `/memory/graph?limit=80` | Returns governed graph with working/review/durable/noise counts |

## 6. Server Verification Commands

Run these on the VPS. They do not print secrets.

```bash
systemctl status bailongma --no-pager -l
systemctl status trendradar-mcp --no-pager -l
systemctl status nginx --no-pager -l
ss -ltnp | grep -E ':(3333|3721|3723|80|443)\b' || true
```

Protected BaiLongma checks:

```bash
PASS=$(awk -F': ' '/^password:/{print $2}' /root/bairui-chat-basic-auth.txt)
curl -sS https://bairui.chat/health
curl -sS -u "owner:$PASS" -H 'Origin: https://bairui.chat' https://bairui.chat/status
curl -sS -u "owner:$PASS" -H 'Origin: https://bairui.chat' https://bairui.chat/settings/voice | python3 -m json.tool
curl -sS -u "owner:$PASS" -H 'Origin: https://bairui.chat' 'https://bairui.chat/memory/graph?limit=80' | python3 -m json.tool
unset PASS
```

Hermes MCP check:

```bash
runuser -u hermes -- env HOME=/home/hermes PATH="/home/hermes/.local/bin:/home/hermes/.hermes/node/bin:/usr/local/bin:/usr/bin:/bin" \
  hermes mcp list
```

Image routing smoke check:

```bash
cd /home/hermes/external/BaiLongma
/home/hermes/.hermes/node/bin/node --input-type=module - <<'JS'
import { selectTools } from './src/memory/tool-router.js'
const tools = selectTools({ messageBody: '帮我识别图片里有什么', mmCaps: [] })
console.log(JSON.stringify({
  hasAnalyzeImage: tools.includes('analyze_image'),
  hasAnalyzeVideo: tools.includes('analyze_video')
}, null, 2))
JS
```

Expected result:

```json
{
  "hasAnalyzeImage": true,
  "hasAnalyzeVideo": false
}
```

Image understanding smoke check:

```bash
cd /home/hermes/external/BaiLongma
runuser -u hermes -- env HOME=/home/hermes PATH="/home/hermes/.hermes/node/bin:/usr/local/bin:/usr/bin:/bin" \
  /home/hermes/.hermes/node/bin/node --env-file=/home/hermes/external/BaiLongma/.env --input-type=module <<'JS'
import fs from 'fs'
import { executeTool } from './src/capabilities/executor.js'
const png = fs.readFileSync('./images/moxi-logo.png')
const dataUrl = `data:image/png;base64,${png.toString('base64')}`
console.log(await executeTool('analyze_image', {
  data_url: dataUrl,
  mode: 'ocr',
  prompt: '请用一句中文说明图片内容。'
}, { currentChannel: 'SYSTEM' }))
JS
```

Expected result:

```text
The result should be ok=true and model=gpt-5.5.
MiniMax is not required for this read-image path. A temporary upstream 502 from the custom model gateway can still make the test fail; retry after the gateway recovers.
```

WeChat inbound image retest:

Owner sends one harmless image to the WeChat ClawBot chat, optionally with a
short caption such as `帮我看看这张图`.

Then check:

```bash
journalctl -u bailongma --since '10 minutes ago' --no-pager \
  | grep -Ei 'ClawBot|saved inbound images|inbound image intake|typing hint|analyze_image|image attachments|工具调用|工具结果' \
  | tail -120
```

Expected result:

```text
ClawBot logs `saved inbound images count=1`, the conversation content contains
`[image attachments]`, and the model calls `analyze_image` before replying.
```

Current performance guard:

- WeChat image tasks are queued with a higher local priority than ordinary user
  turns.
- The queue no longer lets an immediate same-user follow-up replace a pending
  locked image-reading task.
- While an image task is being processed, an ordinary same-priority follow-up
  does not abort it; stronger priority messages can still interrupt.
- ClawBot attempts to send a WeChat typing indicator and logs
  `inbound image intake ms=...` so future latency work can separate WeChat CDN
  download time from model/tool time.

Voice transcript smoke check:

The previous `scripts/smoke-voice-cloud.mjs` helper is not present in the current server checkout. Until it is added, test `/voice/cloud` by opening the Brain UI and speaking a short sentence, or use a temporary project-local WebSocket smoke script that sends 16 kHz mono PCM and expects `asr_status`, `config_ok`, and `transcript`.

```bash
cd /home/hermes/external/BaiLongma
ss -ltnp | grep -E ':(3721|3723)\b' || true
```

Expected result:

```text
3721 listens for BaiLongma backend.
3723 listens for local Whisper after the first local voice session starts.
/voice/cloud returns asr_status, config_ok, and a transcript for real speech.
```

TTS status check:

```bash
PASS=$(awk -F': ' '/^password:/{print $2}' /root/bairui-chat-basic-auth.txt)
curl -sS -u "owner:$PASS" -H 'Origin: https://bairui.chat' https://bairui.chat/settings/tts | python3 -m json.tool
unset PASS
```

Expected result until a provider key is added:

```text
Provider credentials are not configured.
Browser SpeechSynthesis fallback should speak inside Brain UI when cloud /tts/stream fails.
```

If `npm ci` or any Electron-related install step has just run in the BaiLongma
repository, rebuild the Node native SQLite module before restarting the backend:

```bash
cd /home/hermes/external/BaiLongma
runuser -u hermes -- env HOME=/home/hermes PATH="/home/hermes/.hermes/node/bin:/usr/local/bin:/usr/bin:/bin" \
  npm rebuild better-sqlite3 --build-from-source
systemctl restart bailongma
```

Feishu callback smoke check:

```bash
cd /home/hermes/external/BaiLongma

# Public callback must be reachable without the site's Basic Auth.
curl -sS -o /tmp/feishu_wrong -w 'http=%{http_code}\n' \
  -X POST https://bairui.chat/social/feishu/webhook \
  -H 'Content-Type: application/json' \
  --data '{"challenge":"x","token":"x"}'
cat /tmp/feishu_wrong && rm -f /tmp/feishu_wrong

# Service-equivalent env check, without printing secrets.
runuser -u hermes -- env HOME=/home/hermes PATH="/home/hermes/.hermes/node/bin:/usr/local/bin:/usr/bin:/bin" \
  /home/hermes/.hermes/node/bin/node --env-file=/home/hermes/external/BaiLongma/.env --input-type=module <<'JS'
import { env } from './src/social/utils.js'
const token = env('FEISHU_VERIFICATION_TOKEN')
const res = await fetch('https://bairui.chat/social/feishu/webhook', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ challenge: 'challenge_ok', token })
})
console.log('http', res.status)
console.log(await res.text())
JS
```

Expected result:

```text
Wrong token returns 403, not 401.
Correct token returns HTTP 200 with the challenge body.
App ID and App Secret can obtain a Feishu tenant access token.
```

Feishu platform checklist:

- Callback URL: `https://bairui.chat/social/feishu/webhook`
- Event subscription: `im.message.receive_v1`
- Encryption: supported for callback verification and message events when `FEISHU_ENCRYPT_KEY` is configured.
- App visibility/publish state: the bot must be installed or available in the target tenant/chat.
- Bot permissions: grant message receive and send-message permissions, then publish/apply changes if Feishu requires it.


Feishu idempotency and fast-ACK smoke check:

```bash
cd /home/hermes/external/BaiLongma
runuser -u hermes -- env HOME=/home/hermes PATH="/home/hermes/.hermes/node/bin:/usr/local/bin:/usr/bin:/bin" \
  /home/hermes/.hermes/node/bin/node --env-file=/home/hermes/external/BaiLongma/.env --input-type=module <<'JS'
import { getDB } from './src/db.js'
const db = getDB()
console.log(db.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='social_webhook_events'").get())
console.log(db.prepare("SELECT platform, event_type, message_id, status, last_seen_at FROM social_webhook_events ORDER BY last_seen_at DESC LIMIT 5").all())
JS
```

Expected result:

```text
social_webhook_events exists.
Duplicate Feishu event_id/message_id smoke tests return HTTP 200 and are logged once.
Synthetic smoke rows should be cleaned after the test.
```

Feishu company-context smoke check:

```bash
cd /home/hermes/external/BaiLongma
runuser -u hermes -- env HOME=/home/hermes PATH="/home/hermes/.hermes/node/bin:/usr/local/bin:/usr/bin:/bin" \
  /home/hermes/.hermes/node/bin/node --env-file=/home/hermes/external/BaiLongma/.env --input-type=module <<'JS'
import { buildFeishuIdentity, bindFeishuIdentity } from './src/social/feishu-profile.js'
import { resolveCanonicalUserId } from './src/identity.js'

const identity = buildFeishuIdentity({
  sender: { sender_id: { open_id: 'ou_test_person', user_id: 'u_test_person' } },
  message: { chat_id: 'oc_test_group', chat_type: 'group', message_id: 'om_test' },
})
bindFeishuIdentity(identity, { displayName: 'Test Person' })
console.log({
  canonical: identity.canonicalId,
  resolved: resolveCanonicalUserId({ rawFromId: identity.canonicalId, channel: 'FEISHU' }),
  external: identity.externalId,
})
JS
```

Expected result:

```text
canonical and resolved should both be FEISHU:<open_id>, not ID:000001.
For p2p messages, the external delivery target should be feishu:open_id:<open_id>.
For group messages, the external delivery target should be feishu:chat_id:<chat_id>.
```

Feishu group reply route smoke check:

```bash
cd /home/hermes/external/BaiLongma
runuser -u hermes -- env HOME=/home/hermes PATH="/home/hermes/.hermes/node/bin:/usr/local/bin:/usr/bin:/bin" \
  /home/hermes/.hermes/node/bin/node --env-file=/home/hermes/external/BaiLongma/.env --input-type=module <<'JS'
import { executeTool } from './src/capabilities/executor.js'
import { getDB } from './src/db.js'

const marker = `F0 route smoke ${Date.now()}`
const context = {
  currentChannel: 'FEISHU',
  currentExternalPartyId: 'feishu:chat_id:oc_route_smoke_group',
}
try {
  await executeTool('send_message', {
    target_id: 'feishu:open_id:ou_stale_private_target',
    content: marker,
    channel: 'AUTO',
  }, context)
} catch {}
const db = getDB()
const row = db.prepare(`SELECT id, external_party_id FROM conversations WHERE content=? ORDER BY id DESC LIMIT 1`).get(marker)
if (row?.id) db.prepare(`DELETE FROM conversations WHERE id=?`).run(row.id)
console.log(row)
JS
```

Expected result:

```text
The inserted row should use external_party_id = feishu:chat_id:oc_route_smoke_group.
The Feishu API may reject the fake chat_id; that is expected for this synthetic smoke test.
```

Real Feishu group retest:

```text
Owner sends in a real Feishu group: @沫汐 F0群回复测试
Expected: the reply appears in the same group, not in a private chat.
```

Post-test log check:

```bash
journalctl -u bailongma --since '20 minutes ago' --no-pager \
  | grep -Ei 'feishu webhook|Feishu send|send_message|chat_id|open_id|duplicate|async processing' \
  | tail -120
```

## 7. Memory Hygiene During Tests

Before a smoke test:

- Record the current BaiLongma memory count.
- Prefix pure test messages with a clear test label.
- Avoid personal facts, preferences, credentials, or private screenshots.
- Use `skip_recognition` when the turn is only a status check, greeting, or setup test.

After a smoke test:

- Check the memory count again.
- If memory count increased, run a memory dream report before deciding what to change.
- Delete, downgrade, merge, or archive setup noise only after review.
- Put useful setup facts into the phase report, not into permanent memory.

Test output such as `API OK`, `MOXI CORE OK`, `permission fixed`, QR login state, and health-check status should not become durable memory.

Memory dream report command:

```bash
curl -fsS -u "owner:$BAILONGMA_PASS" -H "Origin: https://bairui.chat" \
  "https://bairui.chat/memory/graph?limit=120" > data/memory-graph.json
python scripts/memory-dream.py \
  --input data/memory-graph.json \
  --output data/memory-dream-report.md \
  --source "https://bairui.chat/memory/graph?limit=120"
```

`data/memory-dream-report.md` is ignored by Git by default because it may contain private memory content. Commit only cleaned phase summaries and general governance rules.

## 8. Owner-Facing Capability Test Script

Use this checklist when testing through the UI:

```text
1. Chat: ask one normal Chinese question.
2. Tool: ask for one current trend or search-style result through Hermes/TrendRadar.
3. Image: upload or point to one harmless image and ask for OCR/description.
4. Voice dictation: turn on the microphone button only, speak one short sentence, and confirm it appears in the input box without being sent automatically.
5. Voice conversation: turn on the dialogue button next to the microphone, speak one short sentence, wait for silence auto-send, and confirm the reply is spoken through provider TTS or browser fallback.
6. Memory: ask what it remembers only after the memory count is checked.
7. Dream: generate a memory dream report if the graph looks noisy.
8. Cleanup: remove, merge, or downgrade setup/test memory only after review.
```

Do not use real credentials, financial account screenshots, private contracts, or sensitive customer material in the first test batch.

## 9. Completion Gate

The core phase is considered stable only when:

- Services are active.
- Brain UI is reachable through the protected domain.
- Hermes MCP shows TrendRadar enabled.
- Image route exposes `analyze_image` and hides video.
- Voice route returns a real transcript through local Whisper.
- Brain UI can produce temporary browser speech output, or provider-grade TTS is configured and verified.
- Memory count does not jump because of smoke tests, or a memory dream report identifies and contains the noise.
- Brain UI memory graph shows runtime memory as candidates, with Obsidian marked as source of truth.
- Obsidian write-back workflow exists.
- Chinese phase report is updated.
- Git secret scan finds no committed key, password, token, or QR material.
