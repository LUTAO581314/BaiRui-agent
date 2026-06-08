# Phase 18 - 服务器 Hermes Runtime 与白龙马消息进度桥接

技术路径来源: https://github.com/LUTAO581314/hermes-

## 本阶段目标

把 Phase 17 的前端契约真正落到服务器：让白龙马前端继续使用自己的原生聊天逻辑，但在消息进入白龙马队列之前，先调用 Hermes/MOXI runtime 做 route 判断、自然 ACK、慢任务 job 生命周期记录。

## 已完成

- 在服务器部署并启动 `/opt/hermes-system`。
- `hermes-runtime.service` 已启动，监听 `127.0.0.1:8787`。
- 白龙马 `.env` 已配置：
  - `HERMES_RUNTIME_BASE_URL=http://127.0.0.1:8787`
  - `MOXI_RUNTIME_BASE_URL=http://127.0.0.1:8787`
  - `HERMES_RUNTIME_TIMEOUT_SECONDS=5`
- 白龙马 `/capabilities` 已能显示：
  - `hermes_backend: ready`
  - `hermes_contract: ready`
- 白龙马新增 `/frontend/contract` 代理，浏览器可以从 3721 服务读取 Hermes 前端契约。
- 白龙马 `/message` 已接入 Hermes `/social/turn`：
  - 慢任务先发自然 ACK。
  - 返回 `first_action`、`route`、`ack_sent`、`job_id`。
  - ACK 后向 Hermes `/jobs/event` 上报 `ack_sent`。

## 验证结果

服务器验证通过：

- `systemctl is-active hermes-runtime.service` 返回 `active`。
- `systemctl is-active bailongma.service` 返回 `active`。
- `GET http://127.0.0.1:8787/health` 返回 `status: ok`。
- `GET http://127.0.0.1:3721/frontend/contract` 返回 `ok: true`。
- `POST http://127.0.0.1:3721/message`，内容为 `generate image avatar`，返回：
  - `first_action: quick_ack`
  - `route: image_generate`
  - `ack_sent: true`
  - `job_id` 非空
- `GET http://127.0.0.1:8787/jobs?limit=3` 显示对应 job 从 `queued` 进入 `acknowledged`。

## 当前效果

白龙马前端已经不是 20 秒静默等模型了。对图片生成、看图、搜索、舆情、飞书任务、记忆整理等慢路径，入口处会先得到 Hermes 的自然 ACK，例如“等我拍一下，马上给你～”，然后白龙马原生 Agent loop 继续完成最终回复。

## 仍需优化

- 现在是 ACK 和 job 生命周期打通，最终 worker 的 `worker_started`、`worker_completed`、`final_delivered` 还没有从白龙马原生工具执行链完整上报。
- 前端还需要更细的 progress UI，而不是只靠 ACK 气泡。
- 公司面和个人面 badge 还没有在聊天消息旁边完整展示。
- follow-up “追加到当前慢任务”已经由 Hermes 规划，但白龙马原队列仍需要进一步避免不必要打断。

## 下一步

- 把白龙马工具执行链关键节点接到 `/jobs/event`。
- 前端显示“我在看图 / 搜索 / 生成 / 读飞书”的轻量状态条。
- 给微信、QQ、网页、飞书增加 channel plane badge。
- 导出 Phase 19 progress-aware chat UI patch。
