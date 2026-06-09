# Phase 34 QQ 二维码过期热修阶段报告

## 问题

主人扫码 QQ 个人桥接二维码时提示“二维码过期”。

## 根因

NapCat 每次重启或重新登录会在容器日志里追加新的二维码 URL。原桥接器读取第一条 `二维码解码URL`，当日志里同时存在旧码和新码时，接口可能返回旧二维码，导致扫码提示过期。

## 修复

1. 重启服务器上的 `moxi-napcat` 容器，生成新的 QQ 登录二维码。
2. 修改 `src/social/qq-personal-bridge.js`：
   - 新增 `extractLastMatch(...)`；
   - `extractQrUrl(...)` 改为读取日志里的最后一条二维码 URL；
   - `extractWebuiURL(...)` 同样读取最后一条 WebUI URL。
3. 重启 `bailongma.service`。

## 验证

```text
bailongma.service: active
GET /social/qq-personal/qr -> ok=true, status=qr_ready
```

## 安全说明

本报告不记录真实二维码 URL、WebUI token、QQ 账号 id 或会话文件。它们都属于运行时临时材料，只允许保存在服务器运行目录和容器日志中。

## 主人操作

请在 Brain UI 的 QQ 个人扫码面板点击“查看状态”刷新二维码，然后马上用 QQ 扫码。二维码通常有时效，过几分钟过期是正常的；如果再次过期，就点“启动扫码”或让我重启 NapCat 重新生成。
