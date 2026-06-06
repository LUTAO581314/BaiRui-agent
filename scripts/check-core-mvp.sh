#!/usr/bin/env bash
set -euo pipefail

DOMAIN="${BAILONGMA_DOMAIN:-https://bairui.chat}"
ORIGIN="${BAILONGMA_ORIGIN:-https://bairui.chat}"
USER_NAME="${BAILONGMA_USER:-owner}"

if [[ -z "${BAILONGMA_PASS:-}" && -r /root/bairui-chat-basic-auth.txt ]]; then
  BAILONGMA_PASS="$(awk -F': ' '/^password:/{print $2}' /root/bairui-chat-basic-auth.txt)"
fi

echo "== systemd =="
systemctl is-active bailongma
systemctl is-active trendradar-mcp
systemctl is-active nginx

echo "== ports =="
ss -ltnp | grep -E ':(3333|3721|3723|80|443)\b' || true

echo "== public health =="
curl -fsS "${DOMAIN}/health"
echo

if [[ -n "${BAILONGMA_PASS:-}" ]]; then
  echo "== protected status =="
  curl -fsS -u "${USER_NAME}:${BAILONGMA_PASS}" -H "Origin: ${ORIGIN}" "${DOMAIN}/status"
  echo

  echo "== voice settings =="
  curl -fsS -u "${USER_NAME}:${BAILONGMA_PASS}" -H "Origin: ${ORIGIN}" "${DOMAIN}/settings/voice"
  echo
else
  echo "skip protected checks: set BAILONGMA_PASS or run on the server as a user that can read /root/bairui-chat-basic-auth.txt"
fi

echo "== hermes mcp =="
runuser -u hermes -- env HOME=/home/hermes PATH="/home/hermes/.local/bin:/home/hermes/.hermes/node/bin:/usr/local/bin:/usr/bin:/bin" \
  hermes mcp list

echo "== image route =="
cd /home/hermes/external/BaiLongma
/home/hermes/.hermes/node/bin/node --input-type=module - <<'JS'
import { selectTools } from './src/memory/tool-router.js'
const tools = selectTools({ messageBody: '帮我识别图片里有什么', mmCaps: [] })
console.log(JSON.stringify({
  hasAnalyzeImage: tools.includes('analyze_image'),
  hasAnalyzeVideo: tools.includes('analyze_video')
}, null, 2))
JS

unset BAILONGMA_PASS
