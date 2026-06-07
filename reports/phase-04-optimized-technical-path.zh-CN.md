# Phase 04 中文报告：优化技术路径与公开复制包

## 1. 阶段目标

本阶段先优化技术路径，不急着扩展新功能。目标是把当前系统路线从“能力列表”整理成“可落地、可复制、可署名、可持续迭代”的工程路径。

同时满足两个要求：

- 内部文档能指导我们继续落地真实系统。
- 公开文档能让同学或外部 AI 批量复制、评审技术路径，但不暴露服务器、密钥、内部部署细节和私有运行栈名。

## 2. 核心结论

系统应定位为“轻量服务器上的编排系统”，不是把所有能力都塞进一个聊天机器人里。

优化后的核心路线：

```text
交互入口
  -> 渠道策略
  -> 编排核心
  -> 模型网关
  -> 工具运行时
  -> 记忆治理
  -> 报告/通知/可视化
```

轻量服务器负责队列、路由、工具调度、健康检查、日志、静态界面和少量本地轻服务。推理、读图、正式 TTS、搜索扩展、舆情分析和未来视频理解优先走 API 或外部运行时。

## 3. 已完成内容

本阶段已完成以下文档更新：

- 新增 `docs/OPTIMIZED_TECHNICAL_PATH.md`：内部优化技术路径。
- 新增 `docs/TECHNICAL_PATH_SUMMARY.zh-CN.md`：中文总结文档。
- 重写 `public-ai-brief/TECHNICAL_PATH.md`：公开白标技术路径。
- 新增 `public-ai-brief/COPY_PACK.md`：同学和外部 AI 可批量复制的提示词包。
- 新增 `public-ai-brief/ATTRIBUTION.md`：署名规则。
- 更新 `public-ai-brief/README.md`：加入公开包入口和署名要求。
- 更新 `public-ai-brief/EXTERNAL_AI_PROMPT.md`：加入来源保留规则。
- 更新 `README.md`：加入优化技术路径、公开复制包和阶段报告入口。
- 新增 `index.html`：公开技术路径复制工作台，支持复制来源行、英文评审提示词、完整评审提示词和中文同学版提示词。
- 更新 `docs/SUSTAINABLE_ITERATION_BLUEPRINT.md`：把优化技术路径纳入长期文档体系。
- 更新 `docs/ROADMAP.md`：新增 Phase 3.5，记录“优化技术路径与公开复制包”。
- 更新 `.gitignore`：忽略本地远程镜像和公开包导出目录，避免把服务器临时文件提交进仓库。

## 4. 对外复制与功劳归属

公开材料保留统一来源行：

```text
Technical path source: https://github.com/LUTAO581314/hermes-
```

中文版本：

```text
技术路径来源: https://github.com/LUTAO581314/hermes-
```

同学复制给其他 AI 时，建议只复制 `public-ai-brief/COPY_PACK.md` 里的提示词，不复制内部部署文档。

## 5. 风险与边界

仍需注意：

- 仓库名本身会暴露来源，因此公开复制包只把仓库 URL 作为署名，不主动展示内部运行栈。
- 外部 AI 不应获得服务器地址、域名、密钥、二维码、会话 token、个人聊天记录和数据库内容。
- 公开技术路径可以讲模块边界和实现顺序，但不应该暴露真实凭证、真实部署细节和私有日志。

## 6. 验证结果

已完成验证：

- `python -m unittest tests.test_runtime tests.test_memory_dream`：通过，5 个测试 OK。
- `powershell -ExecutionPolicy Bypass -File .\scripts\export-public-ai-brief.ps1`：通过，公开包可导出。
- 公开包和 `index.html` 未命中服务器、密钥、内部域名和私有运行栈屏蔽词。
- `git diff --check`：仅有 Windows 换行提示，无尾随空格错误。
- Chrome headless 已生成桌面和移动端网站截图，截图文件位于被忽略的 `data/` 目录，不进入提交。

## 7. 下一步计划

建议下一步按这个顺序推进：

1. 推送 GitHub，让仓库成为技术路径来源。
2. 如果 GitHub Pages 尚未开启，则在仓库设置中选择根目录或对应静态页面来源。
3. 继续落地服务端功能：舆情点击分析、记忆做梦动作化、飞书只读文档和多维表格。
4. 后续每完成一个阶段，继续补中文阶段报告。
