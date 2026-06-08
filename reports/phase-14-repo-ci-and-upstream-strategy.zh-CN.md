# Phase 14 - 仓库治理、CI 与上游依赖策略

技术路径来源: https://github.com/LUTAO581314/hermes-

## 本阶段目标

把 `hermes-` 从“规划和运行时仓库”进一步整理成可交给同学和外部 AI 复用的技术路径仓库，同时避免把白龙马整套源码直接塞进主仓库导致维护困难。

## 已落实内容

- 新增 GitHub Actions CI：自动运行 Python 单测、模块编译和仓库卫生检查。
- 删除依赖缺失的旧 conda workflow，避免 GitHub Actions 因没有 `environment.yml` 直接失败。
- 新增 `external/README.md`，说明 BaiLongma 等上游运行时的依赖管理方式。
- 新增 `patches/bailongma/README.md`，把白龙马改造定义为 MOXI overlay，而不是整仓复制。
- 新增 `docs/UPSTREAM_DEPENDENCY_STRATEGY.md`，明确主仓库、上游项目、服务器运行态之间的边界。
- 更新 README 和网站首页，把 CI、上游依赖策略、QQ 连接器、社交 UI 优化纳入公开技术路径。

## 关键决策

白龙马采用“外部上游 + MOXI 补丁/覆盖层”的方式管理。

原因：

- 白龙马是独立 Node/Electron 项目，依赖和发布链路与 `hermes-` 的 Python 轻运行时不同。
- 直接复制全量源码会让仓库变大、升级困难，也不利于同学看清楚哪些是 MOXI 的技术路径。
- MIT License 允许复制和 fork，但必须保留原版权和许可证；当前更适合先保留上游边界。

## 验证方式

本阶段需要验证：

- `python -m unittest discover -s tests`
- `python -m compileall hermes_runtime tests`
- `./scripts/check-repo-hygiene.ps1`

## 后续动作

- 在服务器 BaiLongma 工作区导出第一份正式 patch：社交设置 UI + QQ 配置入口。
- 继续把服务器实际改动沉淀成 `patches/bailongma/*.patch`。
- 如果以后要长期维护白龙马前端，可新建单独 fork，再由 `hermes-` 作为总技术路径仓库引用。

