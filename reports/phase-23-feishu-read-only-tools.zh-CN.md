# Phase 23 飞书只读工具报告

## 本阶段目标

把飞书公司管理从“能聊天、能回群”推进到第一层只读公司数据工具。当前阶段只读，不做创建任务、更新表格、审批、日程写入或公告发送。

## 已完成

- 服务器 BaiLongma 新增 `src/social/feishu-openapi.js`。
- 新增只读 tenant token 封装：
  - 使用 `FEISHU_APP_ID`。
  - 使用 `FEISHU_APP_SECRET`。
  - token 只留在运行时内存，不写入 Git，不返回前端。
- 新增工具：
  - `feishu_lookup_user`。
  - `feishu_bitable_list_records`。
- 新增工具 schema：`src/capabilities/schemas/company.js`。
- 工具路由加入公司/飞书触发词：飞书、通讯录、员工、负责人、多维表格、项目表、任务表等。
- 工具安全策略标记为 low risk，因为它们只读，不写入公司数据。
- 返回结果做了脱敏和截断：
  - 邮箱/手机号只返回是否存在，不返回原文。
  - Bitable 字段最多返回有限数量和长度。
  - 附件或复杂对象只摘要为 `[object]`。

## 验证结果

服务器服务状态：

- `bailongma.service`: active

语法检查：

- `node --check src/social/feishu-openapi.js`: 通过
- `node --check src/capabilities/schemas/company.js`: 通过
- `node --check src/capabilities/schemas.js`: 通过
- `node --check src/capabilities/executor.js`: 通过
- `node --check src/memory/tool-router.js`: 通过
- `node --check src/capabilities/tool-policy.js`: 通过

工具 smoke：

- `getToolSchemas(["feishu_lookup_user", "feishu_bitable_list_records"])` 可以正确返回两个工具 schema。
- `feishu_lookup_user` 在缺少 `user_id` 时返回安全错误。
- `feishu_bitable_list_records` 在未配置 app/table 时返回配置缺口。
- 假 `open_id` 查询返回安全失败和权限提示，不泄漏 token。

## 当前服务器缺口

本次 smoke 显示 `getFeishuReadiness().configured=false`，说明当前 BaiLongma 运行环境没有拿到 `FEISHU_APP_ID` 和 `FEISHU_APP_SECRET`，或当前 service 进程未加载对应配置。

下一步需要确认：

- 飞书 App ID / App Secret 是否已经保存到 BaiLongma 当前运行配置中。
- 应用是否已发布最新版本。
- 是否授予通讯录用户读取权限。
- 是否配置：
  - `FEISHU_BITABLE_APP_TOKEN`
  - `FEISHU_BITABLE_TABLE_ID`
- 机器人是否被加入对应多维表格/空间，具备读取权限。

## 当前意义

Phase 23 已经把工具形状、权限边界、脱敏返回、schema、路由和安全策略搭好。等飞书应用权限和多维表格配置补齐后，沫汐就可以开始回答：

- “这个飞书用户是谁？”
- “这个负责人属于哪个部门？”
- “项目表里现在有哪些任务？”
- “客户/项目/风险表里有哪些待跟进项？”

但她仍然不会自动写入、删除、审批或修改公司数据。

## 官方接口依据

- 自建应用 tenant access token：<https://open.feishu.cn/document/server-docs/authentication-management/access-token/tenant_access_token_internal>
- 获取单个用户信息：<https://open.feishu.cn/document/server-docs/contact-v3/user/get>
- 列出多维表格记录：<https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-record/list>

## 下一步

- Phase 24：在 Brain UI 能力矩阵里显示飞书只读工具 readiness。
- 补齐飞书应用权限和 Bitable app/table 配置后做真实只读查询。
- 再做云文档/文件搜索，只读返回标题、来源链接和摘要。
- 写操作继续保持关闭，直到确认卡片、权限策略和审计日志完成。
