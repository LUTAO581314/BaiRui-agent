#!/usr/bin/env bash
set -euo pipefail

BOT_KEY="${BOT_KEY:-}"
TEXT="${TEXT:-bairui commercial channel trial}"
OUTPUT_PATH="${OUTPUT_PATH:-artifacts/wecom-trial.json}"
RECEIPT_PATH="${RECEIPT_PATH:-artifacts/wecom-receipt.json}"
CREATE_APPROVAL_ONLY="${CREATE_APPROVAL_ONLY:-0}"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --bot-key)
      BOT_KEY="${2:-}"
      shift 2
      ;;
    --text)
      TEXT="${2:-}"
      shift 2
      ;;
    --output-path)
      OUTPUT_PATH="${2:-}"
      shift 2
      ;;
    --receipt-path)
      RECEIPT_PATH="${2:-}"
      shift 2
      ;;
    --create-approval-only)
      CREATE_APPROVAL_ONLY="1"
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

write_json() {
  local path="$1"
  local payload="$2"
  mkdir -p "$(dirname "$path")"
  printf '%s\n' "$payload" > "$path"
}

if [ -n "$BOT_KEY" ]; then
  export BAIRUI_WECOM_TRIAL_BOT_KEY="$BOT_KEY"
  apply_raw="$(python - <<'PY'
import json
import os
from src.hermes.config import load_settings
from src.hermes.config_apply import DANGEROUS_CONFIRMATION_PHRASE, apply_local_config

payload = {
    "danger_confirmation": DANGEROUS_CONFIRMATION_PHRASE,
    "values": {
        "channel_enabled": "1",
        "wecom_bot_key": os.environ.get("BAIRUI_WECOM_TRIAL_BOT_KEY", ""),
    },
}
print(json.dumps({"service": "bairui", "config_apply": apply_local_config(load_settings(), payload)}, ensure_ascii=False))
PY
)"
  unset BAIRUI_WECOM_TRIAL_BOT_KEY
  export BAIRUI_WECOM_APPLY_RAW="$apply_raw"
  apply_status="$(python - <<'PY'
import json
import os
payload = json.loads(os.environ.get("BAIRUI_WECOM_APPLY_RAW", "{}") or "{}")
print(payload.get("config_apply", {}).get("status", ""))
PY
)"
  unset BAIRUI_WECOM_APPLY_RAW
  if [ "$apply_status" != "saved" ]; then
    write_json "$OUTPUT_PATH" "$(python - <<'PY'
import json
print(json.dumps({
    "service": "bairui",
    "mode": "wecom_channel_trial",
    "status": "blocked",
    "secret_echo": False,
    "step": "save_bot_key",
    "next_step": "Check the Bot Key value and rerun the script without printing the secret.",
}, ensure_ascii=False))
PY
)"
    echo "Enterprise WeCom Bot Key could not be saved." >&2
    exit 1
  fi
fi

if ! approval_raw="$(python -m src.hermes channels wecom-trial --text "$TEXT")"; then
  write_json "$OUTPUT_PATH" "$(python - <<'PY'
import json
print(json.dumps({
    "service": "bairui",
    "mode": "wecom_channel_trial",
    "status": "blocked",
    "secret_echo": False,
    "step": "create_approval",
    "next_step": "Configure WECOM_BOT_KEY and rerun the script.",
}, ensure_ascii=False))
PY
)"
  echo "Enterprise WeCom approval creation failed." >&2
  exit 1
fi

if [ "$CREATE_APPROVAL_ONLY" = "1" ]; then
  write_json "$OUTPUT_PATH" "$approval_raw"
  echo "Created Enterprise WeCom test approval only. Output: $OUTPUT_PATH"
  exit 0
fi

if ! send_raw="$(python -m src.hermes channels wecom-trial --text "$TEXT" --approve)"; then
  write_json "$OUTPUT_PATH" "$(python - <<'PY'
import json
print(json.dumps({
    "service": "bairui",
    "mode": "wecom_channel_trial",
    "status": "blocked",
    "secret_echo": False,
    "step": "approve_and_send",
    "next_step": "Check Enterprise WeCom Bot Key/network reachability, then rerun this script.",
}, ensure_ascii=False))
PY
)"
  echo "Enterprise WeCom real send did not produce a sent receipt." >&2
  exit 1
fi

write_json "$OUTPUT_PATH" "$send_raw"
export BAIRUI_WECOM_SEND_RAW="$send_raw"
sent_status="$(python - <<'PY'
import json
import os
payload = json.loads(os.environ.get("BAIRUI_WECOM_SEND_RAW", "{}") or "{}")
review = payload.get("wecom_trial", {}).get("review", {})
sent = bool(review.get("will_send")) and review.get("delivery_status") == "sent" and bool(str(review.get("external_message_id", "")).strip())
print("sent" if sent else "blocked")
PY
)"
receipt_source="$(python - <<'PY'
import json
import os
payload = json.loads(os.environ.get("BAIRUI_WECOM_SEND_RAW", "{}") or "{}")
review = payload.get("wecom_trial", {}).get("review", {})
evidence = review.get("delivery_evidence", {}) if isinstance(review, dict) else {}
print(evidence.get("receipt_path", ""))
PY
)"
unset BAIRUI_WECOM_SEND_RAW

if [ "$sent_status" != "sent" ]; then
  echo "Enterprise WeCom real send did not produce a sent receipt." >&2
  exit 1
fi

mkdir -p "$(dirname "$RECEIPT_PATH")"
if [ -n "$receipt_source" ] && [ -f "$receipt_source" ]; then
  cp "$receipt_source" "$RECEIPT_PATH"
else
  python - "$OUTPUT_PATH" "$RECEIPT_PATH" <<'PY'
import json
import sys
trial_path, receipt_path = sys.argv[1], sys.argv[2]
payload = json.loads(open(trial_path, encoding="utf-8").read())
review = payload.get("wecom_trial", {}).get("review", {})
receipt = {
    "service": "bairui",
    "receipt_type": "channel_delivery",
    "request_id": review.get("request_id", ""),
    "review_id": review.get("review_id", ""),
    "target_id": review.get("target_id", ""),
    "will_send": bool(review.get("will_send")),
    "delivery_status": review.get("delivery_status", ""),
    "external_message_id": review.get("external_message_id", ""),
    "secret_echo": False,
}
open(receipt_path, "w", encoding="utf-8").write(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
PY
fi

echo "Enterprise WeCom channel trial sent. Trial: $OUTPUT_PATH Receipt: $RECEIPT_PATH"
