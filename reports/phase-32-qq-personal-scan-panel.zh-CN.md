# Phase 32 QQ 个人扫码面板阶段报告

## 结论

本阶段在白龙马 Brain UI 的社交通道设置中新增了“QQ 个人扫码”独立面板，把 QQ 官方机器人路线和个人 QQ 扫码桥接路线分开展示。

主人之前的判断是对的：如果走个人 QQ 路线，就应该像微信扫码一样，不应该先让用户填 App ID / Token / Secret。

## 已完成

1. QQ 官方机器人说明补充
   - 保留 App ID、Bot Token、Bot Secret、Webhook Token。
   - 增加说明：这是官方 Bot 路线，适合长期公开服务和权限审计。

2. 新增 QQ 个人扫码面板
   - 新增状态：`social-status-qq-personal`。
   - 新增按钮：
     - 启动扫码
     - 查看状态
     - 断开
   - 新增二维码区域：
     - `qq-personal-qr-area`
     - `qq-personal-qr-img`
     - `qq-personal-qr-hint`
   - 新增反馈：`qq-personal-feedback`。

3. 新增后端占位接口
   - `GET /social/qq-personal/qr`
   - `POST /social/qq-personal/start`
   - `POST /social/qq-personal/logout`

4. 当前状态明确为 planned
   - 服务器还没有安装 NapCat 或 Lagrange 这类 QQ 个人桥接器。
   - 所以启动扫码不会假装可用，而是明确返回 `qq_personal_bridge_missing`。
   - 这样 UI 先把路线分清楚，后续装桥接器后直接接真实二维码。

## 服务器验证

已验证：

```text
GET  http://127.0.0.1:3721/social/qq-personal/qr
POST http://127.0.0.1:3721/social/qq-personal/start
POST http://127.0.0.1:3721/social/qq-personal/logout
```

结果：

```text
/social/qq-personal/qr     -> ok=true, status=bridge_missing, bridge=qq-personal
/social/qq-personal/start  -> HTTP 501, ok=false, error=qq_personal_bridge_missing
/social/qq-personal/logout -> ok=true, status=idle
```

前端资源已验证：

```text
app-shell.js contains qq-personal-connect-btn
app.js contains refreshQQPersonalStatus
```

## 风险与边界

- 本阶段没有安装 QQ 个人协议桥接器。
- 本阶段没有登录 QQ，也没有生成真实 QQ 二维码。
- 没有写入 QQ 账号、cookies、session、token。
- 当前按钮是“路线入口 + 状态提示”，不是假装已经完成 QQ 扫码接入。

## 下一步

真正启用 QQ 个人扫码，需要选型并安装一个桥接器：

1. NapCat QQ：偏现代，适合扫码个人 QQ。
2. Lagrange.OneBot：OneBot 生态兼容更强。

接入后要补：

- 启动桥接器服务。
- 二维码读取接口。
- 登录状态轮询。
- 消息收发适配。
- 掉线重连和风控提示。
- 和 Hermes `/social/turn`、`/jobs/event` 打通。
