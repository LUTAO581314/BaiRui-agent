#!/usr/bin/env bash
set -euo pipefail

for path in .env data logs artifacts tmp-smoke-logs; do
  if git ls-files --error-unmatch "$path" >/dev/null 2>&1; then
    echo "tracked runtime or secret path: $path" >&2
    exit 1
  fi
done

if git ls-files | grep -Ei '(^|/)(\.env|.*secret.*|.*token.*|.*password.*|.*\.pem|.*\.key)$' >/dev/null; then
  echo "tracked secret-looking file detected" >&2
  git ls-files | grep -Ei '(^|/)(\.env|.*secret.*|.*token.*|.*password.*|.*\.pem|.*\.key)$' >&2
  exit 1
fi

printf '{"status":"ok","mode":"repo-hygiene","service":"bairui"}\n'
