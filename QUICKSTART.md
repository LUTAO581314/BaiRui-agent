# MOXI Quickstart

Technical path source: https://github.com/LUTAO581314/hermes-

This quickstart runs the lightweight MOXI control plane only. It does not clone
or run BaiLongma, TrendRadar, Feishu, WeChat, or QQ by itself.

## 1. Clone

```bash
git clone https://github.com/LUTAO581314/hermes-.git
cd hermes-
```

## 2. Create Local Runtime Folders

```bash
mkdir -p data logs obsidian-vault
```

## 3. Start Runtime

```bash
python -m hermes_runtime
```

Default URL:

```text
http://127.0.0.1:8787
```

## 4. Check Health

```bash
curl http://127.0.0.1:8787/health
curl http://127.0.0.1:8787/ready
curl http://127.0.0.1:8787/capabilities
```

## 5. Test Social Turn Planning

```bash
curl -sS http://127.0.0.1:8787/social/turn \
  -H 'content-type: application/json' \
  -d '{"channel":"web","target_id":"web:session:demo","message":"generate image avatar"}'
```

The runtime returns an acknowledgement plan and a job record when the request
should become an async task.

## 6. Connect Upstream Runtimes

MOXI does not replace upstream agent runtimes. It connects them.

- BaiLongma: interaction shell and Brain UI.
- Hermes: native agent logic and tool execution.
- TrendRadar or SearXNG: search and trend intelligence.
- Feishu: company management surface.
- WeChat / QQ: personal and social surfaces.

Use [docs/UPSTREAM_DEPENDENCY_STRATEGY.md](docs/UPSTREAM_DEPENDENCY_STRATEGY.md)
and [patches/bailongma/README.md](patches/bailongma/README.md) for the overlay
boundary.

## 7. What Counts As Success

- `/health` returns `ok`.
- `/ready` returns `ready`.
- `/capabilities` returns a secret-safe matrix.
- `/social/turn` returns a quick acknowledgement plan for slow tasks.
- No real `.env`, logs, media, QR sessions, or API keys are committed.

