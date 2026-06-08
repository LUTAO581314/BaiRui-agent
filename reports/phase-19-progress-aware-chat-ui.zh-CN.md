# Phase 19 - 白龙马前端进度状态条

技术路径来源: https://github.com/LUTAO581314/hermes-

## 本阶段目标

上一阶段已经实现“慢任务先自然 ACK”。本阶段继续补齐前端体验：让用户不只看到一句“我想想/我去看一下”，还可以在聊天界面看到当前任务正在看图、生成图片、搜索、看热点、读飞书或整理记忆。

## 清理结果

服务器 `/home/hermes/external/BaiLongma/src` 里历史备份和临时文件过多，会干扰搜索和 patch 导出。本阶段先完成清理：

- 发现历史 `.bak*`、`*~`、`.tmp` 文件 98 个。
- 已打包归档到 `/home/hermes/backups/bailongma-src-history-backups-20260608174257.tar.gz`。
- `src/` 当前剩余历史备份文件数为 0。
- 临时补丁脚本已删除。
- 清理后 `hermes-runtime.service` 和 `bailongma.service` 均保持 active。

## 已完成

- 白龙马 Brain UI 新增 `moxi-progress` 状态条。
- 前端收到 `moxi_progress` SSE 事件后显示进度。
- 前端收到带 `moxi_progress: true` 的 ACK 消息时，也会同步更新进度。
- 前端收到最终普通 `message` 后，会自动清理进度条。
- 状态条按 Hermes route 显示不同文案：
  - 图片识别：我在看图
  - 图片生成：我在生成图片
  - 搜索：我在查资料
  - 舆情：我在看热点
  - 飞书任务：我在读飞书上下文
  - 记忆任务：我在整理记忆
  - 高风险动作：等待主人确认
- 已导出 overlay patch：
  `patches/bailongma/phase-19-progress-aware-chat-ui.patch`

## 验证结果

服务器验证通过：

- `node --check src/ui/brain-ui/chat.js` 通过。
- `node --check src/ui/brain-ui/app.js` 通过。
- `bailongma.service` 重启后 active。
- `hermes-runtime.service` 保持 active。
- `POST /message` 测试 `generate image avatar` 返回：
  - `first_action: quick_ack`
  - `route: image_generate`
  - `ack_sent: true`
- SSE `/events` 实际收到：
  - ACK `message`，内容为“等我拍一下，马上给你～”
  - `moxi_progress` 事件，状态为 `ack_sent`，route 为 `image_generate`

## 当前效果

现在慢任务的体验从“用户发完后静默等待”升级为：

1. 用户发送消息。
2. Hermes 先判断 route。
3. 白龙马立即显示自然 ACK。
4. 前端显示进度条，例如“我在生成图片”。
5. 白龙马原生 Agent loop 继续生成最终回复。
6. 最终回复出现后进度条自动消失。

## 仍需优化

- 目前完整 worker 生命周期只打通到 `ack_sent`，后续还要把白龙马工具执行链接到 `worker_started`、`worker_completed`、`final_delivered`。
- 前端还没有显示个人面/公司面 badge。
- 连续慢任务时，白龙马原队列仍可能出现 `processing_preempted`，后续需要做 follow-up 合并和打断规则细化。

## 下一步

- Phase 20：公司面/个人面 badge 与确认卡。
- Phase 21：工具执行链生命周期上报。
- Phase 22：follow-up 合并，避免用户补充一句话时打断上一轮慢任务。
