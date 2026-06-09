# Phase 29 Hermes 设置中心重构报告

## 1. 本阶段目标

主人要求设置面板不能只是一组零散表单，而要完整映射 Hermes 的整体配置和运行态，同时允许继续优化 UI。

本阶段先完成第一版“设置中心”重构：把 Brain UI 设置从普通偏好弹窗升级为 MOXI / Hermes 控制台。可写配置继续放在原有模型、媒体、语音、搜索、社交通道、安全页；只读运行态则通过 Hermes 和 BaiLongma 的安全接口展示，不假装拥有尚未实现的写配置能力。

## 2. 已完成改动

服务器 BaiLongma 已部署以下改动：

1. 设置导航重排为：
   - 总览
   - 模型
   - 媒体
   - 语音
   - 搜索
   - 社交通道
   - 记忆
   - 工具任务
   - 安全
   - 外观
   - 更新
2. 新增“总览”页：
   - 显示 Hermes / BaiLongma 控制面说明。
   - 显示能力矩阵。
   - 显示 Hermes `/frontend/contract` 运行契约。
   - 显示 Hermes `/performance` 性能预算。
3. 社交通道页只保留社交连接配置：
   - Discord
   - 飞书
   - 微信公众号
   - 企业微信
   - QQ 官方机器人
   - 微信 ClawBot
4. 新增“记忆”页：
   - 显示运行记忆数量、图节点、图关系。
   - 明确 Obsidian 是长期记忆正本。
   - 明确 dream report 是只读审查，不自动删除或永久写入。
5. 新增“工具任务”页：
   - 显示 Hermes job 数量和事件能力。
   - 明确慢任务、工具调用、审批边界。
6. 设置弹窗 UI 扩大到控制台尺寸，移动端保持自适应。
7. 修复社交通道 HTML 结构中多余闭合标签，避免后续配置块跑出 tab 容器。

## 3. 后端代理补齐

本阶段补了两个只读代理接口：

```text
GET /performance
GET /jobs?limit=N
```

它们通过 BaiLongma 服务器端受保护 Hermes bridge 调用 Hermes runtime，不暴露 Basic Auth、API Key 或运行时密钥。

已有接口继续使用：

```text
GET /capabilities
GET /frontend/contract
GET /status
GET /memory/graph
```

## 4. 服务器部署状态

已部署到：

```text
/home/hermes/external/BaiLongma
```

主要备份：

```text
/home/hermes/backups/bailongma-phase29-settings-console-20260609103324
/home/hermes/backups/bailongma-phase29-hermes-read-proxy-20260609103459
```

服务状态：

```text
bailongma active
```

## 5. 验证结果

服务器侧已验证：

```text
node --check src/ui/brain-ui/app.js
node --check src/ui/brain-ui/app-shell.js
node --check src/api.js
systemctl restart bailongma
systemctl is-active bailongma
```

接口验证结果：

```text
/capabilities 200
/frontend/contract 200
/performance 200
/jobs?limit=2 200
/status 200
/memory/graph?limit=3 200
/src/ui/brain-ui/app-shell.js 200
/src/ui/brain-ui/app.js 200
/src/ui/brain-ui/styles.css 200
```

同时确认：

- 新增中文标签已恢复为可读中文。
- 社交通道页不再承载全局能力矩阵。
- 社交通道 intro 后没有多余 `</div>`。
- patch 文件不包含服务器密码、API key 或 webhook secret。

## 6. GitHub 固化

本阶段导出 overlay patch：

```text
patches/bailongma/phase-29-settings-control-center.patch
```

该 patch 继续遵守上游依赖策略：不复制完整 BaiLongma 源码，只记录 MOXI 对 BaiLongma 的控制台适配。

## 7. 下一步

下一阶段建议补“可写 Hermes 配置中心”：

1. 在 Hermes runtime 增加 secret-safe `GET /config/schema`。
2. 增加受保护的 `POST /config/update`，只允许写白名单配置。
3. 把模型、搜索、语音、图片生成、记忆治理、任务预算都映射到同一套配置 schema。
4. 给高风险配置增加确认步骤和审计日志。
5. 用 Playwright 对设置面板做视觉和 tab 切换 smoke test。
