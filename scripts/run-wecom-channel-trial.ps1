param(
    [string]$BotKey = "",
    [string]$Text = "bairui commercial channel trial",
    [string]$OutputPath = "artifacts/wecom-trial.json",
    [string]$ReceiptPath = "artifacts/wecom-receipt.json",
    [switch]$CreateApprovalOnly
)

$ErrorActionPreference = "Stop"

function Invoke-JsonCommand {
    param(
        [string]$Label,
        [scriptblock]$Command
    )
    try {
        $raw = & $Command | Out-String
        return [pscustomobject]@{
            ok = $true
            label = $Label
            raw = $raw
            payload = ($raw | ConvertFrom-Json)
            error = ""
        }
    }
    catch {
        return [pscustomobject]@{
            ok = $false
            label = $Label
            raw = ""
            payload = $null
            error = "$Label failed: $($_.Exception.Message)"
        }
    }
}

function Write-JsonFile {
    param(
        [string]$Path,
        [object]$Payload
    )
    $parent = Split-Path -Parent $Path
    if ($parent) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    $Payload | ConvertTo-Json -Depth 60 | Set-Content -LiteralPath $Path -Encoding UTF8
}

if ($BotKey.Trim()) {
    $env:BAIRUI_WECOM_TRIAL_BOT_KEY = $BotKey.Trim()
}

$apply = $null
if ($env:BAIRUI_WECOM_TRIAL_BOT_KEY) {
    $apply = Invoke-JsonCommand "save Enterprise WeCom Bot Key" {
        python -c @'
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
'@
    }
    Remove-Item Env:\BAIRUI_WECOM_TRIAL_BOT_KEY -ErrorAction SilentlyContinue
    if (-not $apply.ok -or $apply.payload.config_apply.status -ne "saved") {
        $safeApply = if ($apply.payload) { $apply.payload } else { [pscustomobject]@{ status = "failed"; error = $apply.error } }
        Write-JsonFile -Path $OutputPath -Payload ([pscustomobject]@{
            service = "bairui"
            mode = "wecom_channel_trial"
            status = "blocked"
            secret_echo = $false
            step = "save_bot_key"
            evidence = $safeApply
            next_step = "Check the Bot Key value and rerun the script without printing the secret."
        })
        throw "Enterprise WeCom Bot Key could not be saved."
    }
}

$approval = Invoke-JsonCommand "create Enterprise WeCom test approval" {
    python -m src.hermes channels wecom-trial --text $Text
}

if (-not $approval.ok) {
    Write-JsonFile -Path $OutputPath -Payload ([pscustomobject]@{
        service = "bairui"
        mode = "wecom_channel_trial"
        status = "blocked"
        secret_echo = $false
        step = "create_approval"
        error = $approval.error
        next_step = "Configure WECOM_BOT_KEY and rerun the script."
    })
    throw "Enterprise WeCom approval creation failed."
}

if ($CreateApprovalOnly) {
    Write-JsonFile -Path $OutputPath -Payload $approval.payload
    Write-Output "Created Enterprise WeCom test approval only. Output: $OutputPath"
    exit 0
}

$send = Invoke-JsonCommand "approve and send Enterprise WeCom test message" {
    python -m src.hermes channels wecom-trial --text $Text --approve
}

if ($send.payload) {
    Write-JsonFile -Path $OutputPath -Payload $send.payload
}

$trial = if ($send.payload) { $send.payload.wecom_trial } else { $null }
$review = if ($trial) { $trial.review } else { $null }
$evidence = if ($review) { $review.delivery_evidence } else { $null }
$sent = $send.ok -and $review -and $review.will_send -eq $true -and $review.delivery_status -eq "sent" -and $review.external_message_id

if (-not $sent) {
    $reason = if ($review) { "$($review.delivery_reason) $($review.reason)" } elseif ($send.error) { $send.error } else { "missing delivery receipt" }
    Write-JsonFile -Path $OutputPath -Payload ([pscustomobject]@{
        service = "bairui"
        mode = "wecom_channel_trial"
        status = "blocked"
        secret_echo = $false
        approval = $approval.payload
        send = $send.payload
        error = $reason.Trim()
        next_step = "Check Enterprise WeCom Bot Key/network reachability, then rerun this script."
    })
    throw "Enterprise WeCom real send did not produce a sent receipt."
}

$receiptSource = if ($evidence) { $evidence.receipt_path } else { "" }
if ($receiptSource -and (Test-Path -LiteralPath $receiptSource)) {
    Copy-Item -LiteralPath $receiptSource -Destination $ReceiptPath -Force
}
else {
    Write-JsonFile -Path $ReceiptPath -Payload ([pscustomobject]@{
        service = "bairui"
        receipt_type = "channel_delivery"
        request_id = $review.request_id
        review_id = $review.review_id
        target_id = $review.target_id
        will_send = $review.will_send
        delivery_status = $review.delivery_status
        external_message_id = $review.external_message_id
        secret_echo = $false
    })
}

Write-Output "Enterprise WeCom channel trial sent. Trial: $OutputPath Receipt: $ReceiptPath"
