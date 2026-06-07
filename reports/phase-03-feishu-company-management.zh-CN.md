# Phase 03 中文报告：飞书公司管理整体优化规划

## 1. 阶段目标

本阶段目标是把飞书从“能聊天的机器人入口”升级为“受控的公司管理平面”。

不是一开始就让沫汐自由操作公司，而是先建立：

- 真实飞书消息可靠接入。
- 飞书用户、部门、角色、群聊和项目的身份图谱。
- 只读公司知识能力：云文档、文件、多维表格。
- 公司经营数据表：项目、客户、商机、应收、任务、风险、日报、审批队列、审计日志。
- 主人确认卡片。
- 敏感动作审计和权限边界。

## 2. 参考飞书官方文档后的判断

飞书官方 Agent 集成能力可以拆成三层：

1. 凭据层：一键创建飞书应用，用于快速获得 App ID、App Secret、常见权限和事件订阅。
2. 交互层：Channel SDK 或事件回调，用于让 Agent 在单聊、群聊和文档评论中收发消息。
3. 执行层：飞书 CLI、OpenAPI MCP 或直接 OpenAPI 适配器，用于操作文档、日历、表格、邮件和任务。

对我们来说：

- 应用已经配置过，一键创建不是当前瓶颈。
- 当前主要使用事件回调作为交互层。
- 飞书 CLI/MCP 可以用，但必须放在执行层，并经过权限策略、主人确认和审计日志。
- 稳定、高频、危险边界清晰的能力，后面应优先写成直接 OpenAPI 适配器。

## 3. 当前已完成能力

已完成：

- 飞书公网回调路径：`https://bairui.chat/social/feishu/webhook`。
- Nginx 已对飞书回调路径单独关闭 Basic Auth。
- 支持飞书加密事件。
- 后端可获取 tenant access token。
- 飞书用户已按 `FEISHU:<open_id>` 分离，不再全部映射到主人。
- 单聊回复目标使用 `feishu:open_id:<open_id>`。
- 群聊回复目标使用 `feishu:chat_id:<chat_id>`，避免群里 @ 后回到私信。
- 已新增飞书事件幂等记录表，重复 `event_id` / `message_id` 不再重复执行。
- 已改成快速 ACK + 异步处理，飞书回调先 200，再后台处理。
- 已加当前群聊上下文保护：模型即使误填旧 `open_id`，出站也优先回当前群 `chat_id`。
- 已新增文档：`docs/FEISHU_COMPANY_MANAGEMENT.md`。
- 已把飞书公司管理计划接入 `README.md`、`docs/ROADMAP.md`、`docs/API_INTEGRATIONS.md` 和 `docs/SUSTAINABLE_ITERATION_BLUEPRINT.md`。

## 4. 当前缺口

最关键缺口：

- 还需要主人重新验证真实群聊 @ 消息，确认回复显示在同一个群里，而不是私信。
- 还需要验证身份补丁后的真实单聊消息。
- 还需要在真实事件日志中复核 `external_party_id`：单聊应为 `feishu:open_id:*`，群聊应为 `feishu:chat_id:*`。
- 还没有真实通讯录、部门、角色、群/项目映射。
- 还没有云文档、文件、多维表格只读搜索。
- 还没有公司经营表和日报/周报生成器。
- 还没有飞书卡片确认流。
- 还没有审计日志。
- 还没有任务、日历、审批的安全执行边界。

## 5. 公司管理第一版范围

第一版只做低风险和高价值能力。

应该做：

- 单聊和群 @ 接入。
- 识别是谁、在哪个群、属于哪个项目。
- 读取公司文档和多维表格。
- 回答公司问题时给来源链接。
- 生成每日经营简报。
- 检测延误任务、漏跟进、应收风险和阻塞点。
- 需要改数据时先发给主人确认卡片。

暂时不做：

- 自动审批或拒绝审批。
- 自动发公司公告。
- 自动删除、移动或批量修改文件。
- 自动 HR、财务、合同、法务决策。
- 自动对外承诺。
- 所有群所有消息的全量监听。

## 6. 推荐执行顺序

### F0：聊天可靠性

- 真实单聊 smoke test：待主人复测。
- 真实群 @ smoke test：已发现并修复错回私聊问题，待主人复测。
- 事件幂等：已完成基础实现并通过重复事件烟测。
- 快速 ACK + 异步处理：已完成。
- 日志不泄露密钥。

### F1：公司身份图谱

- 通讯录查询。
- 部门查询。
- 角色映射。
- 群聊和项目绑定。
- 用户和项目绑定。

### F2：只读公司知识

- 搜索云文档。
- 读取文档标题、元信息和摘要。
- 查询多维表格记录。
- 回答带来源链接。

### F3：经营简报 MVP

- 建立项目、客户、商机、应收、任务、风险、日报、审批队列、审计日志表。
- 生成早报和晚报。
- 输出到飞书和 Obsidian。

### F4：确认后的协作动作

- 经确认创建任务。
- 经确认创建日程。
- 经确认写入多维表格。
- 会议纪要和后续任务建议。

### F5：审批和风险

- 读取审批状态。
- 订阅审批事件。
- 提醒主人待审批事项。
- 保持批准/拒绝默认禁用。

### F6：生产硬化

- 权限最小化。
- 工具白名单。
- 速率限制和重试。
- 周度权限审计。
- memory dream 清理飞书测试垃圾。

## 7. 权限策略

第一批权限建议：

- 消息：单聊消息、群 @ 消息、机器人发消息。
- 通讯录：基础用户信息，必要时再加部门信息。
- 文档：只读搜索和元信息读取。
- 多维表格：先只读记录。
- 任务：先只读，创建/更新必须经确认。
- 日历：先只读，创建必须经确认。
- 审批：只读和事件订阅，不批准、不拒绝。

不建议一开始申请全量群消息和大范围编辑权限。

## 8. 结论

现在飞书已经不是“完全没接”，而是“聊天入口、身份分离、事件幂等、快速 ACK 和群聊回复路由第一阶段已完成”。真正公司管理还差三块核心：

1. 可靠性：主人真实复测、真实日志复核、异常重试和监控。
2. 公司数据：通讯录、部门、群/项目、云文档、多维表格。
3. 安全执行：确认卡片、审计日志、权限最小化。

下一步最有价值的是先做 F0 和 F1。只要真实单聊、群 @、身份图谱稳定，后面的文档、表格、简报、任务和审批提醒才不会乱。

## 9. 2026-06-07 F0 落地记录

本次已在服务器 `/home/hermes/external/BaiLongma` 完成飞书 F0 可靠性加固：

- `src/db.js`：新增 `social_webhook_events`，用于记录和拦截重复飞书事件。
- `src/social/webhooks.js`：飞书回调先校验 token 并快速返回 200，再异步处理真实消息。
- `src/social/feishu-profile.js`：群聊事件的出站目标改为 `feishu:chat_id:<chat_id>`，单聊仍使用 `feishu:open_id:<open_id>`。
- `src/capabilities/executor.js`：当前 turn 是飞书群聊时，强制优先回复当前 `chat_id`，防止模型误用旧私聊目标。

验证结果：

- `bailongma` 服务重启后为 active。
- Nginx 为 active。
- `https://bairui.chat/health` 返回 200。
- `executor.js` 通过 Node 语法检查。
- 重复事件烟测已证明第二次重复事件会被忽略。
- 出站路由烟测已证明：即使传入旧 `feishu:open_id`，当前群聊上下文仍会写入并尝试投递到 `feishu:chat_id`。

待主人操作：

- 在飞书真实群里发送：`@沫汐 F0群回复测试`。
- 如果回复出现在群里，F0 群聊路由可以标记通过。
- 如果仍然回私信，需要立刻查看最新 `journalctl -u bailongma` 和最近 `conversations` 记录。

## 10. 官方参考链接

- 飞书 Agent 集成能力：<https://open.feishu.cn/document/mcp_open_tools/overview-of-lark-agent-integration-capabilities>
- 飞书 OpenAPI MCP 概述：<https://open.feishu.cn/document/mcp_open_tools/mcp-overview?lang=zh-CN>
- 接收消息事件：<https://open.feishu.cn/document/server-docs/im-v1/message/events/receive?lang=zh-CN>
- 发送消息：<https://open.feishu.cn/document/server-docs/im-v1/message/create?lang=zh-CN>
- 事件订阅概述：<https://open.feishu.cn/document/server-docs/event-subscription-guide/overview?lang=zh-CN>
- 批量获取用户信息：<https://open.feishu.cn/document/contact-v3/user/batch?lang=zh-CN>
- 云文档概述：<https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/docx-overview?lang=zh-CN>
- 多维表格概述：<https://open.feishu.cn/document/server-docs/docs/bitable-v1/bitable-overview?lang=zh-CN>
