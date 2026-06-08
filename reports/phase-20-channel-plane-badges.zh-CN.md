# Phase 20 - 聊天界面 Channel Plane Badge

技术路径来源: https://github.com/LUTAO581314/hermes-

## 本阶段目标

在 Phase 18/19 已经完成“先 ACK、再显示进度”的基础上，本阶段补齐权限和通道可见边界。用户在聊天界面里应该能一眼看出当前消息属于个人陪伴、网页陪伴、公司管理、Runtime 进度，还是需要主人确认的高风险动作。

## 已完成

- 白龙马 Brain UI 的 `addMsg` 新增 `channel`、`route`、`plane`、`badge` 参数。
- 气泡新增 `msg-plane-badge`。
- 通道自动映射：
  - 微信、QQ：个人陪伴
  - 网页：网页陪伴
  - 飞书、Lark、企微：公司管理
- route 自动覆盖：
  - `company_task` 显示公司管理
  - `high_risk` 显示主人确认
  - `moxi_progress` ACK 可显示 Runtime/进度上下文
- 前端 `message` 和 `message_in` 事件已把 channel/route 传给聊天气泡。
- 已导出 overlay patch：
  `patches/bailongma/phase-20-channel-plane-badges.patch`

## Runtime 同步优化

本阶段发现中文消息“帮我看一下飞书项目任务”在 route classifier 中缺少中文关键词覆盖。已补充 Hermes runtime 中文路由词：

- 图片识别
- 图片生成
- 搜索
- 舆情/热点
- 飞书/公司任务
- 记忆整理
- 高风险动作

并新增回归测试，确保中文飞书任务命中 `company_task`，中文表情包生成命中 `image_generate`。

## 验证结果

- 本地 `python -m unittest discover -s tests` 通过。
- 本地 `python -m compileall hermes_runtime tests` 通过。
- 服务器 `node --check src/ui/brain-ui/chat.js` 通过。
- 服务器 `node --check src/ui/brain-ui/app.js` 通过。
- `hermes-runtime.service` active。
- `bailongma.service` active。
- 服务器 `/route` 对中文飞书任务返回 `company_task`。
- 使用 JSON Unicode escape 的 `/message` 测试返回：
  - `first_action: quick_ack`
  - `route: company_task`
  - `ack_sent: true`

## 当前效果

现在白龙马前端不只是“能回复”，还开始具备 Agent 控制台该有的权限可视化：个人陪伴、公司管理、网页聊天、Runtime 进度和主人确认不会再混成一类消息。

## 下一步

- Phase 21：把白龙马工具执行链关键节点上报到 Hermes `/jobs/event`，补齐 `worker_started`、`worker_completed`、`final_delivered`。
- Phase 22：处理 follow-up 合并，避免用户补充一句话时打断上一轮慢任务。
