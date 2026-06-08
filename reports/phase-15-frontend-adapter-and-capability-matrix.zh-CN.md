# Phase 15 - Hermes 前端适配与能力矩阵

技术路径来源: https://github.com/LUTAO581314/hermes-

## 本阶段目标

进入下一阶段整体优化：不重写 Hermes 的原生 agent 逻辑，而是把 MOXI 做成接入层、前端适配层、能力体检层和权限隔离层。

## 已完成

- 新增 `/capabilities` 能力矩阵 endpoint。
- 新增 `hermes_runtime/capabilities.py`，统一输出文本、图片、搜索、记忆、微信、飞书、QQ、语音、TTS、表情、生图等能力状态。
- 新增 `docs/CAPABILITY_MATRIX.md`，定义前端如何渲染 ready / partial / missing_config / disabled / planned。
- 新增 `docs/HERMES_FRONTEND_ADAPTER_PLAN.md`，明确 Hermes、MOXI runtime、BaiLongma/Brain UI 的职责边界。
- 新增 `QUICKSTART.md`，让同学能快速跑最小控制平面。
- 更新公开首页和 README，把能力矩阵、前端适配和 Quickstart 加入入口。

## 关键判断

Hermes 不是被替代对象，而是上游 agent runtime。MOXI 的价值在于：

- 把多 channel 消息规范化；
- 给前端提供真实能力状态；
- 把慢任务变成可见的 ACK + job lifecycle；
- 把个人陪伴和公司管理做权限隔离；
- 把可复制技术路径沉淀到 GitHub。

## 下一步

- 从服务器 BaiLongma 工作区导出第一份真实 patch：社交设置 UI + QQ 入口 + 能力矩阵展示。
- 在 Brain UI 设置面板里接入 `/capabilities`。
- 增加前端 progress state：思考中、看图中、生成中、搜索中、公司数据读取中。
- 把 Feishu 公司身份映射状态也暴露成 secret-safe capability。

