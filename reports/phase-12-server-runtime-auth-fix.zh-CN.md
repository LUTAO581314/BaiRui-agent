# Phase 12 中文报告：服务器 Runtime 调用认证修复

## 1. 问题现象

主人反馈“用不了了”。检查后确认：

- 本地单元测试通过；
- 本地 runtime 的 `/health`、`/social/turn`、`/jobs/event` 都正常；
- 公网 `bairui.chat` 主服务健康；
- 但直接调用公网 `/social/turn` 和 `/jobs` 返回 `401 Unauthorized`。

这说明问题不是 runtime 代码坏了，而是服务器公网入口有 Basic Auth，连接器客户端没有携带认证头。

## 2. 修复内容

更新 `hermes_runtime/connector_client.py`：

- 支持 `basic_username`；
- 支持 `basic_password`；
- 新增 `HermesConnectorClient.from_env()`；
- 自动从环境变量读取：
  - `HERMES_RUNTIME_BASE_URL`
  - `HERMES_RUNTIME_TIMEOUT_SECONDS`
  - `HERMES_RUNTIME_BASIC_USER`
  - `HERMES_RUNTIME_BASIC_PASSWORD`
- 调用服务器公网 runtime 时自动添加 `Authorization: Basic ...`。

本机调用仍然支持：

```python
HermesConnectorClient("http://127.0.0.1:8787")
```

服务器公网调用改为：

```python
client = HermesConnectorClient.from_env()
```

真实凭据必须通过服务器环境变量注入，不写入仓库。

## 3. 文档更新

更新 `docs/CONNECTOR_INTEGRATION_RUNBOOK.md`，明确：

- 调本机 runtime 不需要认证；
- 调服务器受保护公网入口时必须配置 Basic Auth 环境变量；
- 如果缺少认证变量，会出现 `401 Unauthorized`。

## 4. 验收结果

- 单元测试通过，当前共 21 个测试。
- 编译检查通过。
- 新增测试覆盖 `from_env()` 和 Basic Auth header。
- 未提交真实服务器密码、API Key 或私密地址。

Technical path source: https://github.com/LUTAO581314/hermes-
