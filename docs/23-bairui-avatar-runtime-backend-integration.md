# bairui Avatar Runtime 后端集成说明

## 目标

本阶段只集成浏览器 Avatar Runtime 的后端契约，不实现前端渲染。

前端默认使用 `pixi-live2d-display-advanced` 作为 Live2D 浏览器渲染引擎。后端负责：

- 暴露引擎元数据和安装提示。
- 管理 Live2D 模型资源目录。
- 校验 `.model3.json` 模型包和引用资源。
- 生成前端可读的 Avatar manifest。
- 记录 Agent 状态到 Avatar 状态的切换事件。
- 提供只读模型资源访问。

后端不负责 WebGL 渲染，也不直接执行 PixiJS。

## 默认引擎

```txt
package: pixi-live2d-display-advanced
version: ^1.1.0
license: MIT
runtime: PixiJS/WebGL
fallback: pixi-live2d-display
```

后端把该项目固定为 bairui Avatar Runtime 的默认浏览器引擎。前端后续只需要读取 `/avatar/manifest`，再在自己的构建环境里安装该 npm 包。

## 环境变量

```txt
BAIRUI_AVATAR_ASSETS_DIR=./data/avatars
BAIRUI_AVATAR_PUBLIC_BASE_URL=
BAIRUI_AVATAR_DEFAULT_MODEL=
BAIRUI_AVATAR_ENGINE_PACKAGE=pixi-live2d-display-advanced
BAIRUI_AVATAR_ENGINE_VERSION=^1.1.0
```

说明：

- `BAIRUI_AVATAR_ASSETS_DIR`：模型包和贴图资源根目录。
- `BAIRUI_AVATAR_PUBLIC_BASE_URL`：可选公网资源前缀；为空时后端使用 `/avatars/assets/...`。
- `BAIRUI_AVATAR_DEFAULT_MODEL`：默认模型 manifest，相对 `BAIRUI_AVATAR_ASSETS_DIR`。
- `BAIRUI_AVATAR_ENGINE_PACKAGE`：默认前端引擎包名。
- `BAIRUI_AVATAR_ENGINE_VERSION`：默认前端引擎版本范围。

## HTTP API

### GET /avatar/status

返回浏览器 Avatar 引擎契约。

用途：

- 设置页展示 Avatar Runtime 状态。
- 激活页确认 Avatar 功能是否可用。
- 前端构建或部署页面提示需要的 npm 包。

### GET /avatar/manifest

返回前端渲染所需 manifest。

包含：

- `brand: bairui`
- engine 元数据
- 模型路径和 URL
- 模型校验结果
- WebGL / lip sync 运行说明
- 状态到 motion/expression 的默认映射

### POST /avatar/validate

请求：

```json
{
  "model_path": "default/bairui.model3.json"
}
```

返回：

- `valid`
- `missing_assets`
- `invalid_manifest`
- `not_found`

校验内容：

- `.model3.json` 是否存在。
- `FileReferences.Moc` 是否存在。
- `Textures` 是否存在。
- `Motions` 是否存在。
- `Expressions` 是否存在。

### POST /avatar/state

请求：

```json
{
  "avatar_id": "default",
  "state": "speaking",
  "text": "主人，文档摄取已经完成。",
  "audio_url": "/media/tts/example.wav",
  "lip_sync": true
}
```

允许状态：

```txt
idle
thinking
speaking
approval_required
error
done
hidden
```

该接口会写入审计事件 `avatar.state_changed`。前端后续可以把它和 `/events` 组合成实时 Avatar 状态流。

### GET /avatars/assets/*

从 `BAIRUI_AVATAR_ASSETS_DIR` 只读返回模型资源。

安全约束：

- 路径必须位于 Avatar 资源根目录内。
- 禁止路径越界。
- 不存在资源返回 `404`。

## CLI

```txt
python -m src.hermes avatar status
python -m src.hermes avatar manifest
python -m src.hermes avatar manifest --model-path default/bairui.model3.json
python -m src.hermes avatar validate --model-path default/bairui.model3.json
python -m src.hermes avatar state --state speaking --text "ready"
```

## 前端接入边界

前端后续只需要做三件事：

1. 安装 `pixi-live2d-display-advanced`。
2. 读取 `/avatar/manifest` 加载模型。
3. 根据 `/avatar/state` 或后续事件流切换动作、表情和嘴型。

第一版嘴型建议使用 Web Audio API 音量驱动 `ParamMouthOpenY`。后端只提供 `audio_url`、`state=speaking` 和 `lip_sync=true`。

## 产品定位

Avatar 是 bairui 的可选形象层，不是核心功能阻塞项。

推荐呈现位置：

- 激活页引导员。
- 工作台右下角 Agent Dock。
- Avatar 设置页。

不建议让 Avatar 遮挡图谱、文档工作台、记忆审核和渠道审批等核心操作区。
