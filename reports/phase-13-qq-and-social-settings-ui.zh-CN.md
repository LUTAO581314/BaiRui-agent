# Phase 13 中文报告：QQ 通道与社交设置前端优化

## 1. 问题背景

主人指出当前社交媒体设置里没有 QQ，并询问前端能不能优化。

检查后确认：

- 当前仓库此前只优先规划了飞书、企业微信、微信 ClawBot 和网页聊天。
- QQ 没有被加入第一批通道，不是因为做不了，而是之前优先级没排到。
- 截图里的设置 UI 源码不在当前 `hermes-` 仓库；当前仓库只有公开技术路径页面和 runtime 代码。

## 2. QQ 为什么之前没有

QQ 属于第三个社交入口，应排在 runtime 合同稳定之后接入。

推荐路线是 QQ 官方机器人，而不是一开始就做非官方个人号自动化。

原因：

- 官方 Bot 更适合长期运行和 webhook 接入。
- 可复用当前 `/social/turn` 和 `/jobs/event`。
- 风险边界比个人号自动化清楚。
- 高风险公司动作仍然不应该从 QQ 直接执行。

## 3. 已完成修复

新增 QQ runtime 配置字段：

- `HERMES_QQ_MODE`
- `HERMES_QQ_BOT_APP_ID`
- `HERMES_QQ_BOT_TOKEN`
- `HERMES_QQ_BOT_SECRET`
- `HERMES_QQ_WEBHOOK_TOKEN`

`/health` 新增 `qq` 状态块，只显示是否配置，不返回真实密钥。

新增 `docs/QQ_CONNECTOR.md`，定义：

- QQ 缺失原因；
- 推荐接入路线；
- QQ target id 规范；
- connector flow；
- 安全边界；
- 前端设置需求。

## 4. 前端优化方案

新增 `docs/SOCIAL_SETTINGS_UI_OPTIMIZATION.md`。

建议把当前“长表单堆叠”改成：

- Channel overview 卡片网格；
- Feishu 独立详情页；
- WeCom 独立详情页；
- WeChat ClawBot 独立详情页；
- QQ Official Bot 独立详情页；
- Runtime Connector 独立认证面板。

前端必须明确显示：

- Connected；
- Missing credentials；
- Needs scan；
- Webhook blocked；
- Auth failed；
- Disabled。

并为每个渠道提供：

- Test Connection；
- Copy Webhook；
- Save Channel；
- Last Check；
- Error Mapping。

## 5. 当前边界

本阶段完成的是 runtime 配置、文档和 UI 优化规范。截图里的真实设置面板源码不在当前仓库，所以还没有直接改到线上前端组件。

要真正改截图里的 UI，需要拿到对应前端源码目录或服务器项目路径，然后按 `SOCIAL_SETTINGS_UI_OPTIMIZATION.md` 落地组件。

## 6. 验收结果

- QQ 已进入 runtime 配置和健康检查。
- QQ 接入方案已写入文档。
- 前端设置优化方案已写入文档。
- README 和公开技术路径已更新。
- 单元测试覆盖 QQ 配置加载和 `/health` 脱敏输出。

Technical path source: https://github.com/LUTAO581314/hermes-
