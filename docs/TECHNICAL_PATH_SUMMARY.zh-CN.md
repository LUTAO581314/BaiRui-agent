# 技术路径优化总结

## 1. 本次优化结论

当前系统最合理的路线不是继续把能力堆进一个聊天机器人，而是把它整理成一个轻量服务器上的 Agent 编排系统。

核心结构：

```text
交互入口
  -> 渠道策略
  -> 编排核心
  -> 模型网关
  -> 工具运行时
  -> 记忆治理
  -> 报告/通知/可视化
```

轻量服务器只负责路由、队列、健康检查、日志、工具调度、静态页面和少量轻服务。大模型推理、读图、正式 TTS、搜索扩展、舆情分析和未来视频理解优先走 API 或外部运行时。

## 2. 关键架构优化

- 从“聊天入口”升级为“统一任务编排”：网页、微信、飞书、CLI 都先转成标准任务。
- 从“单模型”升级为“模型插槽”：fast、summary、reasoning、vision、asr、tts 分工明确。
- 从“什么都记”升级为“记忆治理”：工作记忆、做梦整理、人工审核、Obsidian 长期记忆分层。
- 从“看起来有面板”升级为“可追溯工作台”：热点、舆情、记忆图、图片和语音都要有来源、状态和动作。
- 从“直接执行”升级为“权限分级”：读、草稿、通知、写入、敏感动作、不可逆动作分层控制。

## 3. 对外复制方案

给同学或外部 AI 使用 `public-ai-brief/`，不要直接复制内部部署文档。

公开材料必须保留来源：

```text
Technical path source: https://github.com/LUTAO581314/hermes-
```

中文来源：

```text
技术路径来源: https://github.com/LUTAO581314/hermes-
```

这样可以让别人批量复制技术路径，但功劳和来源仍然回到我们的仓库。

## 4. 本次交付文件

- `docs/OPTIMIZED_TECHNICAL_PATH.md`：内部优化技术路径。
- `docs/TECHNICAL_PATH_SUMMARY.zh-CN.md`：给主人看的中文总结文档。
- `public-ai-brief/TECHNICAL_PATH.md`：公开白标技术路径。
- `public-ai-brief/COPY_PACK.md`：同学和外部 AI 可复制提示词。
- `public-ai-brief/ATTRIBUTION.md`：署名规则。
- `index.html`：公开技术路径复制工作台。
- `reports/phase-04-optimized-technical-path.zh-CN.md`：阶段中文报告。

## 5. 验证结果

- 公开包导出脚本已通过。
- 公开包未命中服务器、密钥、内部域名和私有运行栈屏蔽词。
- 本地单元测试通过。
- `git diff --check` 仅提示 Windows 换行警告，无尾随空格错误。
- 网站桌面和移动端截图已用 Chrome headless 生成并检查；截图保存在被忽略的 `data/` 目录，不提交。

## 6. 下一步

1. 推送 GitHub，让仓库成为技术路径来源。
2. 如需公开访问网站，在 GitHub Pages 里选择仓库根目录的 `index.html`。
3. 继续实现舆情点击分析、记忆做梦动作化、飞书只读文档和多维表格。
4. 每个阶段继续写中文报告。
