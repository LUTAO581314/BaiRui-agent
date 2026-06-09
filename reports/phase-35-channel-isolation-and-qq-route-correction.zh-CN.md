# Phase 35 通道隔离与 QQ 路线纠偏阶段报告

## 背景

本阶段发现两个问题：

1. 主人在网页 Brain UI 里询问，回复却被投递到了微信。
2. QQ 个人扫码路线被误当成“机器人绑定”，实际 NapCat 二维码是个人 QQ 客户端登录。

## 问题 1：网页消息串到微信

### 现象

网页/API 发出的消息进入队列后，模型调用 `send_message`，最终被投递到 `wechat-clawbot`。

### 根因

系统把同一个主人身份合并成 `ID:000001`。当模型显式选择或推断到微信通道时，`send_message` 会从 presence/历史外部身份里找到微信 ClawBot 目标，导致网页会话跨通道投递。

### 修复

服务器热修 `src/capabilities/executor.js`：

- 如果当前 turn 的通道归一化为 `TUI`，直接强制本地投递。
- 即使模型传入 `WECHAT` / `FEISHU` / `AUTO`，也不能从网页/API/语音 turn 泄漏到社交平台。
- 跨通道发送必须以后做成显式用户确认动作。

### 验证

```text
POST /message channel=API
send_message -> ID:000001 [TUI]
未出现 wechat-clawbot 外部投递
```

## 问题 2：QQ 路线纠偏

### 纠正

NapCat / Lagrange 这类 OneBot 路线扫码，本质是登录一个个人 QQ 客户端或个人号协议桥，不是“绑定官方 QQ 机器人”。

MOXI 的默认 QQ 路线应改为：

1. QQ 开放平台创建官方机器人。
2. 配置 AppID / Token / AppSecret。
3. 选择 Webhook 或 WebSocket 事件接收。
4. 在 QQ 端把机器人添加到群/频道/会话。
5. BaiLongma/Hermes 只处理机器人事件和回复。

NapCat 只能保留为“个人号实验路线”，默认关闭，不再作为 QQ 主线。

## 新规则

- Web / API / Brain UI / Voice：只回本地界面或语音，不自动发微信、QQ、飞书。
- 微信入站：只回当前微信上下文。
- 飞书入站：群里 @ 就回群，私聊就回私聊。
- QQ 官方机器人入站：只回机器人事件来源。
- 跨通道转发：必须主人显式确认。

## 后续

下一阶段应把 QQ 设置面板改成：

- `QQ 官方机器人`：主路线，配置 AppID / Token / AppSecret / Webhook。
- `QQ 个人号实验`：默认折叠，标明“登录个人 QQ，不是机器人绑定”。
- 对 NapCat 启动按钮增加强风险提示。
