#!/usr/bin/env bash
set -euo pipefail

ROOT="${BAILONGMA_ROOT:-/home/hermes/external/BaiLongma}"
DOMAIN="${BAILONGMA_DOMAIN:-https://bairui.chat}"

if [[ ! -d "$ROOT" ]]; then
  echo "BaiLongma root not found: $ROOT" >&2
  exit 2
fi

cd "$ROOT"

echo "== probe target =="
pwd
echo

echo "== frontend hardcoded local API references =="
grep -RInE "127\.0\.0\.1:3721|localhost:3721|http://127\.0\.0\.1|http://localhost|settings/voice|new EventSource|/events" \
  src/ui public . \
  --exclude-dir=node_modules \
  --exclude-dir=.git \
  --exclude='*.map' \
  2>/dev/null | sed -n '1,220p' || true
echo

echo "== likely brain ui files =="
find src/ui public -type f \
  \( -iname "*brain*" -o -iname "app.js" -o -iname "chat.js" -o -iname "*.html" \) \
  -not -path "*/node_modules/*" \
  2>/dev/null | sort | sed -n '1,120p' || true
echo

echo "== public endpoint checks =="
curl -k -sS -o /dev/null -w "health %{http_code} %{content_type}\n" "$DOMAIN/health" || true
curl -k -sS -o /dev/null -w "brain-ui %{http_code} %{content_type}\n" "$DOMAIN/brain-ui.html" || true
curl -k -sS -o /tmp/moxi-events-probe.txt -w "events %{http_code} %{content_type}\n" \
  --max-time 5 --http1.1 "$DOMAIN/events" || true
head -c 240 /tmp/moxi-events-probe.txt 2>/dev/null || true
echo

echo "== local service checks =="
ss -ltnp | grep -E ':(3721|80|443)\b' || true
systemctl is-active bailongma 2>/dev/null || true
systemctl is-active nginx 2>/dev/null || true
echo

echo "== nginx sse hints =="
grep -RInE "location .*events|proxy_buffering|X-Accel-Buffering|http2|3721" \
  /etc/nginx/sites-enabled /etc/nginx/conf.d \
  2>/dev/null | sed -n '1,180p' || true
echo

echo "== result hint =="
echo "If frontend files contain 127.0.0.1:3721, replace browser-side API base with same-origin relative paths."
echo "If /events fails over HTTP/2, configure the Nginx /events location for SSE: proxy_http_version 1.1, proxy_buffering off, X-Accel-Buffering no."
