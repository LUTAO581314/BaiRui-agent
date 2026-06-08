# Phase 10 中文报告：慢任务 Worker 生命周期事件

## 1. 本阶段目标

本阶段目标是把慢任务从“有状态机”推进到“连接器可直接上报生命周期事件”。真实微信、飞书或网页连接器不应该手写状态转换表，而应该只上报发生了什么，例如 ACK 已发送、worker 已开始、worker 已完成、最终消息已投递。

## 2. 已完成内容

新增 job 事件枚举：

```text
ack_sent
worker_started
worker_completed
worker_failed
final_delivered
failure_delivered
cancel_requested
```

新增事件到状态的映射：

```text
ack_sent -> acknowledged
worker_started -> running
worker_completed -> completed
worker_failed -> failed
final_delivered -> delivered
failure_delivered -> failure_delivered
cancel_requested -> cancelled
```

新增运行时接口：

```text
POST /jobs/event
```

连接器只需要提交：

```json
{
  "job_id": "...",
  "event": "worker_completed",
  "result_pointer": "asset://image/result"
}
```

runtime 会自动校验状态转换是否合法，并更新 job。

## 3. 对微信和飞书的意义

真实链路可以变成：

1. `/social/turn` 返回 quick ACK 和 job。
2. 渠道发送 ACK 成功后上报 `ack_sent`。
3. worker 开始执行时上报 `worker_started`。
4. worker 成功后上报 `worker_completed`，并写入结果指针。
5. 最终消息投递成功后上报 `final_delivered`。
6. 如果失败，上报 `worker_failed`，失败说明投递后上报 `failure_delivered`。

这样微信、飞书、网页前端都可以共享同一套慢任务生命周期，不需要每个连接器重复实现状态机。

## 4. 隐私与安全

事件上报只保存：

- job id；
- event；
- 状态；
- 时间戳；
- result pointer；
- error message 摘要。

不保存消息正文、截图、API 原始响应、密钥、服务器信息或工具原始输出。

## 5. 验收结果

- 新增 `POST /jobs/event`。
- `/jobs` 返回允许的事件列表。
- 单元测试覆盖 `ack_sent -> worker_started -> worker_completed -> final_delivered` 完整成功链路。
- 总测试数提升到 19 个，全部通过。
- 文档和公开技术路径已更新。

Technical path source: https://github.com/LUTAO581314/hermes-
