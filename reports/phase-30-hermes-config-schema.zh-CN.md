# Phase 30 Hermes 可写配置 Schema 阶段报告

## 结论

本阶段完成了 Hermes runtime 的 secret-safe 可写配置 schema。Brain UI
以后不需要硬编码所有设置项，可以通过 Hermes 的控制面接口读取配置结构、
渲染字段、保存白名单配置，并且不会把 API key、密钥或高风险运行参数暴露给前端。

## 已完成

1. 新增 `GET /config/schema`
   - 返回模型、搜索、媒体/表情、生图、社交性能预算四组配置字段。
   - 每个字段包含类型、当前值、选项、范围、是否可写、是否 secret。
   - secret 字段只返回 `configured`，不返回真实值。

2. 新增 `POST /config/update`
   - 只允许白名单配置键。
   - 拒绝未知键，例如 `HERMES_HOST`。
   - 拒绝非法选项、非法布尔值、越界整数。
   - 空 secret 更新表示保持原值。
   - 写入 `HERMES_CONFIG_ENV_PATH` 指定的 env 文件；未指定时写入 `.env.hermes-runtime`。
   - 写入后刷新当前进程 `RuntimeConfig`，前端保存后可立即看到新状态。

3. 更新 `/frontend/contract`
   - 声明 `config_schema` 和 `config_update` 两个端点。
   - 白龙马/Brain UI 可以通过 contract 发现配置接口，不需要猜路径。

4. 增加测试
   - schema 不泄密。
   - 合法更新会写入 env 文件并刷新 runtime。
   - 未知键、非法选项、越界数值会被拒绝。

## 本阶段白名单

已开放：

- 模型网关：provider、base URL、API key、default/fast/summary/reasoning/vision 模型、timeout。
- 搜索：search mode、search project、TrendRadar base URL、SearXNG base URL。
- 媒体：表情桥、默认 provider、默认风格、表情 API key、生图开关、生图 base URL、生图模型、审核开关、缓存开关。
- 性能：快速 ACK 延迟、快速回复目标、慢任务阈值、异步任务超时、延迟遥测开关。

暂不开放：

- host、port。
- data/log/Obsidian 路径。
- safe mode。
- 高风险系统开关。

这些配置后续可以做“高级模式 + 主人确认 + 备份回滚”，但不应该在第一版普通设置面板直接写。

## 对前端的影响

白龙马前端下一步应当：

1. 通过 `/frontend/contract` 获取 `config_schema` 和 `config_update` 路径。
2. 调用 `/config/schema` 渲染设置页。
3. secret 输入框只显示“已配置/未配置”，保存时只提交用户新填的值。
4. 保存后调用 `/config/update`，再刷新 schema、health、performance。
5. 对未知键和非法值显示清晰错误，不要静默失败。

## 验证

已通过：

```text
python -m unittest discover -s tests
python -m compileall hermes_runtime tests
```

测试结果：

```text
Ran 29 tests
OK
```

## 风险与下一步

当前 Hermes 侧配置控制面已经完成。下一阶段建议做白龙马前端 overlay：

- 在设置面板增加“运行配置”页，动态渲染 Hermes schema。
- 白龙马服务代理 `/config/schema` 和 `/config/update`。
- 保存前显示变更摘要。
- 对 secret 字段做“留空保持原值”的 UI 提示。
- 每次保存前自动备份服务器 env 文件到 `/home/hermes/backups`。
