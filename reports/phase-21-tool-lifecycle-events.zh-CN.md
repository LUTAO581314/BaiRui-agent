# Phase 21 工具生命周期事件报告

## 本阶段目标

把 BaiLongma 原生处理链路接回 Hermes `/jobs/event`，让慢任务不再只停留在
`ack_sent`，而是可以继续进入：

- `worker_started`
- `worker_completed`
- `worker_failed`
- `final_delivered`

## 已完成

- 在服务器 BaiLongma 新增共享 runtime bridge：
  `src/moxi-runtime-bridge.js`。
- 在 `runTurn` 中上报原生 worker 开始、完成和失败。
- 在 `send_message` 最终消息送达路径中上报 `worker_completed` 和
  `final_delivered`。
- 将 Hermes job 元数据传入工具执行上下文：
  `hermesJobId`、`hermesPlanRoute`、`hermesFirstAction`。
- 向 Brain UI 的 `moxi_progress` 事件同步 lifecycle 状态，方便前端显示
  “正在处理 / 已完成 / 已送达”。
- 清理服务器 BaiLongma 历史备份垃圾和 Python 缓存，保持 `src` 内
  `.bak*`、`*~`、`.tmp` 为 0。
- 导出 focused overlay patch：
  `patches/bailongma/phase-21-tool-lifecycle-events.patch`。

## 验证结果

服务器服务状态：

- `bailongma.service`: active
- `hermes-runtime.service`: active

语法检查：

- `node --check src/moxi-runtime-bridge.js`: 通过
- `node --check src/index.js`: 通过
- `node --check src/capabilities/executor.js`: 通过

真实链路 smoke：

- 通过 BaiLongma `POST /message` 发送 Feishu 风格中文任务。
- 返回 `first_action=quick_ack`，route 为 `company_task`，并创建 Hermes job。
- job 最终进入 `delivered`。
- `result_pointer` 为 `conversation:<id>`，只保存元数据指针，不保存原始消息、
  平台 token、API key、图片或文件内容。

## 当前意义

Phase 18 只做到 “先自然 ACK，然后进入队列”。Phase 21 补上了后半段：
BaiLongma 原生 Agent 真的开始处理、处理完成、最终回复可见之后，Hermes 都能知道。

这让前端不需要猜状态，也让微信、QQ、飞书后续可以共用同一套进度模型：

```text
/social/turn -> ack_sent -> worker_started -> worker_completed -> final_delivered
```

## 风险与边界

- 现在的 `final_delivered` 以“写入会话并发出本地 UI 事件”为准；外部平台投递失败时
  仍需要后续阶段细分 `failure_delivered`。
- 当前 patch 是 overlay，不把 BaiLongma 全量源码复制进本仓库。
- 所有密钥、真实 chat id、二维码会话、API key 继续留在服务器运行环境，不进入 Git。

## 下一步

- Phase 22：处理 follow-up 合并和取消语义，让用户连续补充信息时不会误打断慢任务。
- 继续优化 Feishu company plane：通讯录身份、群项目映射、只读云文档/多维表格。
- 给 Brain UI 增加更明确的 lifecycle 视觉反馈和失败恢复入口。
