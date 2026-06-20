#!/usr/bin/env bash
set -euo pipefail

paths=(
  "web/bairui-console/index.html"
  "web/bairui-console/app.js"
  "web/bairui-console/app-shell.js"
  "web/bairui-console/chat.js"
  "web/bairui-console/wechat-popup.js"
  "src/hermes/frontend_contract.py"
)

for path in "${paths[@]}"; do
  [[ -f "$path" ]] || { echo "missing brand scan target: $path" >&2; exit 1; }
done

if grep -RInE 'Hermes|MOXI|BaiLongma|白龙马|小白龙|FunASR|MinerU|TrendRadar|MiroFish|SearXNG|Sonic|EverOS|Obsidian' "${paths[@]}"; then
  echo "forbidden public brand exposure detected" >&2
  exit 1
fi

if ! grep -RIn 'bairui' "${paths[@]}" >/dev/null; then
  echo "bairui public brand marker missing" >&2
  exit 1
fi

printf '{"status":"ok","mode":"public-brand","service":"bairui"}\n'
