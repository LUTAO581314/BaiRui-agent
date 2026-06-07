# 飞书公司管理方案

## 1. 当前定位

飞书是公司管理平面。微信保持个人陪伴和低风险提醒。Obsidian 保持长期记忆正本。Hermes 与 MOXI 运行时把飞书当成项目、客户、任务、日程、文档、审批和经营报告的操作空间。

当前飞书集成已经完成第一层：聊天入口、身份识别和 F0 可靠性基础。

- 公网回调地址已验证：`https://bairui.chat/social/feishu/webhook`。
- Nginx 只对飞书回调路径关闭站点 Basic Auth，不放开整个站点。
- 已支持飞书加密回调。
- 后端可以获取飞书 tenant access token。
- 飞书发送者已按 `FEISHU:<open_id>` 分离，不再全部合并成主人用户。
- 单聊回复投递到 `feishu:open_id:<open_id>`；群聊回复投递到 `feishu:chat_id:<chat_id>`。
- 已增加飞书事件幂等表，按事件/消息去重，避免飞书重试造成重复执行。
- 已改成快速 ACK + 异步处理，回调先返回 200，再进入后端处理。
- 已加群聊回复保护：当前 turn 是飞书群聊时，即使模型误填旧的 `open_id`，出站也强制回当前 `chat_id`，避免群里 @ 后私聊回复。

这说明“聊天可靠性基础”已经具备，但还不能算真正的公司管理。

## 2. 飞书能力分层

飞书官方 Agent 集成能力适合拆成三层理解：

| 层级 | 飞书能力 | 本项目用法 |
| --- | --- | --- |
| 凭据层 | 一键创建应用 | 可选捷径。现在应用已经配置过，不是当前瓶颈。 |
| 会话层 | Channel SDK 或事件回调 | 接收用户消息、群 @、卡片交互，并把结果回复到飞书。 |
| 执行层 | 飞书 CLI、OpenAPI MCP 或直接 OpenAPI 适配器 | 受控调用文档、日程、多维表格、任务、审批等工具。 |

正确路线不是让 CLI 直接暴露给所有人，而是：

```text
飞书消息或事件
  -> 渠道路由
  -> 身份和群/项目解析
  -> 意图识别
  -> 权限和风险策略
  -> 只读工具或审批后的写入工具
  -> 审计日志
  -> 飞书回复、卡片、报告或 Obsidian 写回
```

## 3. 我们还差什么

### 3.1 真实消息验证

回调、加密 challenge、事件幂等、快速 ACK 和群聊回复路由已经验证。真实群里 @ 曾经到达服务器，但当时暴露出“群聊消息被私聊回复”的路由问题；该问题已修复，仍需要主人重新做一次真实群聊复测。

还要完成：

- 主人给机器人发一条真实单聊消息。
- 在群里 @ 机器人发一条真实消息，并确认回复出现在同一个群里。
- 确认真实 `open_id`、`user_id`、`union_id`、`chat_id`、`chat_type`、`message_id` 写入正确。
- 复核重复事件不会重复写会话或重复发消息。

### 3.2 身份、组织和角色

现在只是“不把所有飞书用户混成一个人”。还没有真正理解公司组织。

还要完成：

- 通讯录查询真实显示名。
- 部门查询。
- 角色映射：主人、管理者、员工、财务、销售、外部联系人。
- 群聊和项目绑定。
- 用户和项目绑定。
- 明确谁能请求哪些动作。

### 3.3 群聊上下文

公司工作主要发生在群里，不是单聊里。

还要完成：

- 识别机器人是否被 @。
- 保留群 `chat_id` 和项目上下文。当前基础路由已做到群聊回复使用 `chat_id`，下一步要补群/项目映射。
- 维护短期话题上下文，但不把原始聊天都写成长期记忆。
- 默认在忙碌群里只响应 @。
- 对敏感内容转私聊给主人确认。

### 3.4 文件、云文档和知识库

公司管理离不开文件。第一版必须只读。

第一阶段能力：

- 搜索可见云文档。
- 列出配置好的云空间文件夹。
- 读取文档标题、元信息和正文摘要。
- 回答时带来源链接。
- 不自动复制敏感内容到长期记忆。

第一版不要启用删除、移动、批量改文档等动作。

### 3.5 多维表格经营数据

只靠聊天无法管理公司。需要结构化经营表。

第一批建议建一个公司经营多维表格，包含：

| 表 | 用途 |
| --- | --- |
| Projects | 项目、负责人、状态、里程碑、下一步、风险等级 |
| Customers | 客户、联系人、负责人、阶段、下次跟进、备注 |
| Sales Pipeline | 商机、金额、概率、预计成交、阻塞点 |
| Receivables | 应收款、金额、到期日、状态、提醒记录 |
| Tasks | 任务、负责人、截止时间、状态、来源、关联项目/客户 |
| Risks | 风险、严重度、负责人、缓解措施、复盘时间 |
| Daily Reports | 日期、亮点、阻塞、决策、明日计划 |
| Approval Queue | 请求动作、请求人、风险等级、主人决策、执行结果 |
| Audit Log | 操作者、动作、工具、输入摘要、输出摘要、确认记录 |

### 3.6 任务和日程

只读数据稳定后，再加协作动作。

可做：

- 从飞书消息创建任务。
- 在批准范围内更新任务状态。
- 查询当天日程。
- 起草会议议程。
- 经确认后创建会议。
- 生成会议纪要和后续任务。

### 3.7 审批边界

审批能力强，也危险。

第一版只做：

- 读取审批状态。
- 订阅审批状态事件。
- 提醒主人待处理审批。
- 总结审批上下文。

默认不允许 agent 自主批准、拒绝或提交敏感审批。

### 3.8 飞书 CLI / MCP 的位置

飞书 CLI 和 OpenAPI MCP 可以用，但它们是执行层，不是入口层。

建议：

- 稳定、窄范围、高频工作用直接 OpenAPI 适配器。
- 探索性、只读、开发者使用场景可用飞书 CLI/MCP。
- 两者都必须经过同一个权限策略和审计日志。
- 写入、删除、审批、公告等危险工具先禁用，等白名单和确认卡片做好再开。

### 3.9 飞书卡片和主人确认

纯文本不适合公司控制。

需要的卡片：

- 经营简报卡片。
- 任务确认卡片。
- 审批请求卡片。
- 风险预警卡片。
- 报告交付卡片。

敏感卡片必须有确认/取消路径，并写入审计记录。

### 3.10 监控和治理

还要补：

- 飞书事件日志检查命令。
- 后端事件队列健康检查。
- 工具调用成功/失败统计。
- 周度权限审查。
- 飞书测试后做 memory dream 清理，避免测试垃圾进入长期记忆。

## 4. 推荐阶段

### F0：聊天可靠性

目标：真实飞书消息稳定进来、能回复、不会重复执行。

交付：

- 真实单聊 smoke test。待主人复测。
- 真实群 @ smoke test。已发现并修复错回私聊问题，待主人复测。
- 事件幂等。已完成基础表和重复事件拦截。
- 快速 ACK + 异步处理。已完成。
- 不泄露秘密的失败日志。持续保持。

### F1：公司身份图谱

目标：沫汐知道是谁在说话、属于哪个部门、在哪个项目群。

交付：

- 通讯录查询。
- 部门查询。
- 角色映射。
- 群/项目映射。
- UI 和日志显示可读身份。

### F2：只读公司知识

目标：沫汐能从飞书文档和表格回答公司问题。

交付：

- 云文档搜索。
- 文件夹列表。
- 多维表格列表和记录查询。
- 带来源的回答。
- 默认不写入、不删除、不改状态。

### F3：公司简报 MVP

目标：主人每天收到真正有用的公司简报。

交付：

- 项目/客户/任务/风险表。
- 早报。
- 晚报。
- 延误任务识别。
- 漏跟进识别。
- 报告写入飞书和 Obsidian。

### F4：协作动作

目标：沫汐能在确认后帮助维护工作项。

交付：

- 经确认创建任务。
- 起草会议议程。
- 经确认创建日程。
- 会议纪要。
- 后续任务建议。

### F5：审批和风险工作流

目标：沫汐成为受控运营助手，而不是失控执行器。

交付：

- 审批状态读取。
- 审批事件订阅。
- 主人确认队列。
- 敏感动作卡片。
- 审计日志。

### F6：生产硬化

目标：公司管理进入稳定运行。

交付：

- 权限最小化。
- 速率限制和重试策略。
- 工具白名单。
- 周度审计报告。
- 阶段中文报告和 memory dream 清理。

## 5. 权限计划

先从最小权限开始。

| 区域 | 第一批权限 |
| --- | --- |
| 消息 | 接收单聊、接收群 @、机器人发消息 |
| 通讯录 | 基础用户信息，必要时再加部门信息 |
| 云文档/搜索 | 优先读取可见文档和搜索结果 |
| 云空间 | 列出配置文件夹、读取元信息 |
| 多维表格 | 先读记录；写入和管理等表结构锁定后再开 |
| 任务 | 先读任务；创建/更新必须经过确认策略 |
| 日历 | 先读日程；创建日程必须确认 |
| 审批 | 先读状态和订阅事件；批准/拒绝保持禁用 |

不要一开始申请“所有群所有消息”或大范围编辑权限，除非主人明确接受风险。

## 6. 立即执行顺序

下一步不应该直接做审批自动化，而是：

1. 请主人在真实飞书群里发送：`@沫汐 F0群回复测试`，确认回复是否回到同一个群。
2. 验证一条真实飞书单聊事件。
3. 检查真实事件日志和最近会话，确认 `external_party_id` 使用正确的 `open_id` 或 `chat_id`。
4. 增加飞书公司上下文配置。
5. 增加只读多维表格记录查询。
6. 增加只读文档搜索。
7. 生成第一份基于真实飞书数据的主人简报。

这样能先产生公司管理价值，同时不把危险权限过早交给 agent。

## 7. 官方参考链接

- 飞书 Agent 集成能力：<https://open.feishu.cn/document/mcp_open_tools/overview-of-lark-agent-integration-capabilities>
- 飞书 OpenAPI MCP 概述：<https://open.feishu.cn/document/mcp_open_tools/mcp-overview?lang=zh-CN>
- 接收消息事件：<https://open.feishu.cn/document/server-docs/im-v1/message/events/receive?lang=zh-CN>
- 发送消息：<https://open.feishu.cn/document/server-docs/im-v1/message/create?lang=zh-CN>
- 事件订阅概述：<https://open.feishu.cn/document/server-docs/event-subscription-guide/overview?lang=zh-CN>
- 事件加密配置：<https://open.feishu.cn/document/server-docs/event-subscription-guide/event-subscription-configure-/encrypt-key-encryption-configuration-case?lang=zh-CN>
- 批量获取用户信息：<https://open.feishu.cn/document/contact-v3/user/batch?lang=zh-CN>
- 云文档概述：<https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/docx-overview?lang=zh-CN>
- 云空间文件概述：<https://open.feishu.cn/document/docs/drive-v1/file/file-overview>
- 搜索文档：<https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/search-v2/doc_wiki/search?lang=zh-CN>
- 多维表格概述：<https://open.feishu.cn/document/server-docs/docs/bitable-v1/bitable-overview?lang=zh-CN>
- 查询多维表格记录：<https://open.feishu.cn/document/docs/bitable-v1/app-table-record/search?lang=zh-CN>
- 创建多维表格记录：<https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-record/create?lang=zh-CN>
- 创建任务：<https://open.feishu.cn/document/task-v2/task/create?lang=zh-CN>
- 创建日程：<https://open.feishu.cn/document/server-docs/calendar-v4/calendar-event/create?lang=zh-CN>
- 审批事件概述：<https://open.feishu.cn/document/server-docs/approval-v4/event/function-introduction?lang=zh-CN>
- 审批实例概述：<https://open.feishu.cn/document/server-docs/approval-v4/instance/overview-approval-instance?lang=zh-CN>
