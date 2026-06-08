# Phase 09 中文报告：慢任务追问不打断策略

## 1. 本阶段目标

本阶段解决一个真实社交场景问题：用户发图、生图、搜索或飞书任务后，又马上补一句话。如果系统把补充消息当成新任务，上一轮慢任务就可能被打断、重复创建或丢失最终结果。

目标是让同一微信/飞书会话里的追问只追加到未完成任务，不取消、不重复建 job。

## 2. 已完成内容

新增 `AsyncJobStore.active_for_target(channel, target_id)`，可以查询同一渠道和目标里最近的未完成任务。

活跃状态包括：

```text
queued
acknowledged
running
```

`POST /social/turn` 现在会先检查活跃任务：

- 如果没有活跃任务，按原逻辑路由、ACK、创建 job。
- 如果有活跃任务，且用户不是明确取消，就返回 `append_to_active_job`。
- 如果用户明确取消，例如 `cancel`、`stop`、`取消`、`别做`、`停下`，后续可走取消流程。

## 3. 返回行为

追问时返回：

```json
{
  "first_action": "append_to_active_job",
  "ack": {
    "should_send": true,
    "text": "刚才那件事没丢，我把这句一起算进去～",
    "counts_as_final": false
  },
  "active_job": {
    "job_id": "..."
  }
}
```

payload 仍然不保存追问正文，只返回输入长度预览和活跃 job 元数据。

## 4. 对实际体验的影响

这会直接改善主人之前指出的慢体验：

- 发图后又问“你能看到吗”，不会打断读图任务。
- 生图时又补充“可爱一点”，不会重复创建第二个生图 job。
- 搜索/舆情任务还没完成时，补充条件会被视为同一任务的上下文增量。
- 飞书公司任务处理中，补充信息会跟随原任务，不会乱开新流程。

## 5. 验收结果

- 新增活跃任务查询。
- `/social/turn` 支持 `append_to_active_job`。
- 单元测试覆盖同一会话追问不创建第二个 job。
- ACK 文案已修为运行时干净中文，源码使用 ASCII Unicode escape，避免 Windows/PowerShell 编码污染。
- 测试通过。

Technical path source: https://github.com/LUTAO581314/hermes-
