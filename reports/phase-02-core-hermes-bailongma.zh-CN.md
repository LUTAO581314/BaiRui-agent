# Phase 02 中文报告：核心 Hermes + MOXI Brain UI MVP

## 1. 阶段目标

本阶段先解决核心闭环，而不是一次性接满所有能力：

- Hermes 编排核心稳定运行。
- MOXI Brain UI 能稳定访问和交互。
- 主模型走已配置的 OpenAI-compatible 网关。
- TrendRadar 作为外部搜索、RSS、趋势和舆情运行时。
- 记忆治理保持“工作记忆 -> 审核 -> Obsidian 正本”的路线。
- 图片理解、语音输入、工具调用进入核心验证范围。

本阶段仍不把视频理解、AI 视频生成、自动交易、飞书公司管理和未授权语音克隆当作已完成能力。

## 2. 已完成事项

- `bairui.chat` 已代理到 MOXI Brain UI。
- 后端服务、nginx、TrendRadar MCP 均处于运行状态。
- Brain UI 可见品牌名和 `/agent-profile` 均为 `MOXI`。
- 已使用主人提供的头像图作为 MOXI 左上角 Logo。
- 热点按钮已可打开热点/舆情面板。
- `/hotspots` 已返回抖音、小红书、微信热点、微博四个平台热榜。
- 热点标题已改为可点击：有原始 URL 时打开原始 URL；没有 URL 时走对应平台搜索兜底。
- TrendRadar 最新本地输出已接入热点面板底部事件流，新闻/RSS 卡片可点击原文。
- 本地 Whisper tiny 已作为过渡 ASR。
- 图片理解工具 `analyze_image` 已接入当前主模型，并已用 GPT-5.5 网关直接读图成功。
- Brain UI 聊天框已支持选择、粘贴、拖拽图片附件，图片会进入 `analyze_image` 读图链路。
- WeChat ClawBot 入站图片已接入同一条读图链路：服务端下载微信图片媒体、保存到 sandbox 上传目录，再让模型调用 `analyze_image`。
- Brain UI 记忆图是只读工作记忆视图，不替代 Obsidian 长期记忆。

## 3. 2026-06-07 更新记录

本轮修复了主人指出的两个实际体验问题：

1. 热点新闻标题点不动。
   - 根因：前端 `hotspot.js` 把标题渲染成普通 `<span>`，并且 normalize 时丢掉了后端保留的 `url` 字段。
   - 修复：标题改为安全外链 `<a>`；保留 `url/platform/source`；无 URL 时按平台生成搜索链接。

2. 舆情项目爬到的内容没有显示在面板里。
   - 根因：TrendRadar 已经在服务器产出 `output/news/*.db` 和 `output/rss/*.db`，但 `/hotspots` 只返回四个平台热榜，没有把外部趋势输出并入 UI。
   - 修复：`/hotspots` 新增 `feed` 数组，读取 TrendRadar 最新 news/RSS 输出；Brain UI 底部事件流优先显示真实 `feed`，失败时才回退到原 mock 数据。

同时完成：

- 上传 `moxi-logo.png` 到 Brain UI 静态目录。
- `app-shell.js` 左上角品牌标记改为头像 Logo。
- CSS 增加 Logo、热榜链接、舆情 feed 链接样式。
- 修复一次上传中断导致远端 `hotspot.js` 变成 0 字节的问题，并改用 base64 + 原子替换方式上传。

## 4. 验证结果

已验证：

- `https://bairui.chat/health` 返回正常。
- `bailongma` 服务为 active。
- MOXI Logo 图片：`200 image/png`，大小 `497267` 字节。
- `app-shell.js` 包含 `/src/ui/brain-ui/moxi-logo.png`。
- `hotspot.js` 包含 `hs-item-link`、`hotspotFeed`、`hs-feed-title-link`。
- `styles.css` 包含 `brand-mark-logo`、`hs-item-link`、`hs-feed-title-link`。
- `/hotspots` 平台数量：
  - 抖音：49
  - 小红书：20
  - 微信热点：50
  - 微博：50
- `/hotspots.feed` 返回 16 条 TrendRadar 新闻/RSS 事件。
- TrendRadar feed 状态：`ok: true`，source 为 `trendradar-output`。
- 第一条 feed 有可点击 URL。
- 本地测试：`python -m unittest tests.test_runtime tests.test_memory_dream`，5 个测试通过。

## 5. 当前缺口

- 热点面板现在能展示 TrendRadar 已爬内容，但还没有做“点某条 -> 触发 5.4 mini/5.4/5.5 分层分析 -> 生成舆情报告”的完整动作链。
- 当前网页语音输出已切换为浏览器 SpeechSynthesis only，不再依赖云端 TTS key；声音质量和可选音色取决于浏览器与系统。
- 读图不需要 MiniMax；Brain UI 图片附件和 WeChat 入站图片都走 GPT-5.5 视觉能力。MiniMax 仍可作为后续生图、音乐、歌词或正式 TTS 供应商。`image2` 生图仍然不可用，因为它属于图片生成 provider，不是 GPT-5.5 读图能力。
- 飞书聊天凭证已配置并通过回调验证；飞书公司管理 MVP 还没开始。
- Obsidian 写回仍以文档流程为主，还需要做成 Hermes 工具。
- 自动交易仍不进入可执行范围，只能做研究、提醒、模拟和风控报告。

## 6. 2026-06-07 语音聊天排查记录

本轮排查了主人指出的“网页里仍然无法语音聊天：语音识别 + TTS”问题。

结论：

- 语音识别不是当前主故障。本地 Whisper tiny 已在服务器通过 `/voice/cloud` 完整验证，返回 `asr_status`、`config_ok` 和真实 transcript。
- 原 TTS 主故障是供应商凭证未配置，`/tts/stream` 会返回 500；主人确认当前阶段只依赖浏览器 TTS。
- 前端此前只有普通整段 TTS 失败会走浏览器兜底；流式逐句朗读路径失败后可能跳过句子，导致网页对话容易“静音”。

已完成修复：

- `src/ui/brain-ui/app.js` 已设置 `BROWSER_TTS_ONLY = true`，网页对话朗读直接走浏览器 SpeechSynthesis。
- “聊”按钮开启时会先触发一句浏览器语音试听，用于解锁浏览器发声权限。
- TTS 设置页的“试听”按钮也改为浏览器语音试听，不再请求 `/tts/stream`。
- 服务器已重启 `bailongma`，公网资源已确认包含 `BROWSER_TTS_ONLY`、`unlockBrowserSpeech` 和 `isVoiceReplyEvent`。
- `https://bairui.chat/health` 返回 200，`/status` 返回 running。

当前能力边界：

- “听”：本地 Whisper 可用。
- “说”：网页使用浏览器自带声音，不需要 MiniMax/豆包/OpenAI TTS key。
- “正式 TTS”：仅当后续需要更高音质、更稳定音色或跨浏览器一致性时，再配置 MiniMax、豆包、OpenAI TTS、ElevenLabs 或其他批准供应商的 key。

## 7. 2026-06-07 实时语音对话按钮更新

主人反馈：当前网页能实时听见语音，但表现更像“语音转文字到输入框”，不知道什么时候会进入实时对话。

已完成更新：

- 在 MOXI Brain UI 左侧顶部麦克风按钮旁新增“聊”按钮。
- 麦克风按钮只负责语音输入/听写。
- “聊”按钮负责实时对话模式：开启后，语音最终识别文本会在停顿后自动发送，并触发回复朗读。
- “聊”按钮关闭时，语音只转文字进入输入框，不自动发送，适合听写和人工编辑。
- 开启“聊”按钮时，会自动打开麦克风，并同步打开“识别后自动发送”设置。
- 空格 PTT 松开发送也遵守“聊”按钮：对话模式开才发送，关则保留听写文本。

验证结果：

- `bailongma` 服务重启后为 active。
- `https://bairui.chat/brain-ui.html` 返回正常页面。
- 服务器文件已包含 `voice-dialogue-btn`、`VOICE_DIALOGUE_MODE_KEY` 和 `getDialogueMode` 逻辑。
- 已在服务器保留 `*.bak.voice-dialogue-20260607094024` 备份。

## 8. 下一阶段建议

## 8.1 2026-06-07 微信图片读取入口更新

主人追问：“微信界面可以发吗”。本轮先补齐微信入站图片读取，不把它和语音、视频、文件混在一起做。

已完成：

- 服务器 `/home/hermes/external/BaiLongma/src/social/wechat-clawbot.js` 已增加图片媒体处理。
- ClawBot 收到微信图片 item 后，会通过 `wechat-ilink-client` 的 `client.downloadMedia(item)` 下载并解密图片。
- 图片最多处理 4 张，单张最大 8MB，保存到 BaiLongma sandbox 的 `uploads/images` 目录。
- 入队消息会附带 `[image attachments]`，并明确要求模型调用 `analyze_image`，再结合用户文字回复。
- 该能力复用当前 GPT-5.5 视觉网关，不需要 MiniMax。
- 服务器已备份原文件，执行 `node --check src/social/wechat-clawbot.js` 通过。
- `bailongma` 服务已重启并保持 `active`。
- `https://bairui.chat/health` 返回 `200`。
- 重启后日志显示 ClawBot 已恢复保存的凭证和 context token。
- 真实微信图片复测已通过：ClawBot 保存图片、消息带 `[image attachments]`、模型调用 `analyze_image` 成功，并已通过微信回复主人。

当前边界：

- 代码、语法、服务健康、ClawBot 启动都已验证。
- 首次复测中，主人紧接着追问“你能看到这个图片吗”导致上一轮图片处理被打断并重试，所以体感变慢。
- 微信语音消息还没有作为完整语音聊天处理；后续要单独接入 ASR。
- 微信仍只作为个人陪伴入口，不用于公司审批、资金、HR、法务或交易动作。

性能第一版优化：

- 微信图片任务现在使用更高本地优先级。
- 队列不会让同一用户的后续普通消息覆盖尚未处理完的图片读取任务。
- 图片读取任务处理中，普通同级追问不会中断该任务；更高优先级任务仍可中断。
- ClawBot 会尝试发送微信 typing 指示，让微信端出现“正在输入/思考中”的体感。
- 日志新增 `inbound image intake ms=...`，后续可区分微信 CDN 下载耗时、模型视觉耗时和最终发送耗时。
- 服务器已备份 `src/social/wechat-clawbot.js`、`src/queue.js`、`src/index.js`，远程 `node --check` 均通过，`bailongma` 重启后为 `active`，`https://bairui.chat/health` 返回 `200`。

## 9. 2026-06-07 沫汐人格与自我认知更新

主人要求：Agent 不要再把自己认知为“小白龙”、Hermes 或 BaiLongma，而要使用新的亲密陪伴人格“沫汐”。

已完成更新：

- 服务器数据库 `config.agent_name` 已改为 `沫汐`。
- 服务器数据库 `config.persona` 已写入“沫汐 - 自我认知与陪伴人格”。
- Persona 中加入硬规则：日常对话身份只能是“沫汐”；Hermes、BaiLongma、MOXI 只能作为后台项目名、技术组件名或品牌名解释。
- `src/index.js` 默认 agent 名兜底从“小白龙”改为“沫汐”。
- `src/api.js` 和 Brain UI `app.js` 默认显示名兜底改为“沫汐”。
- 已处理 UTF-8 写入问题，数据库校验显示 `agent_name` 的 codepoint 为 `6cab 6c50`，即“沫汐”，不是 `??`。
- 服务器已重启 `bailongma`，公网健康检查返回 `200`。

当前边界：

- 对话身份应使用“沫汐”。
- 技术文档仍可能保留 Hermes、BaiLongma、MOXI 作为架构/项目名，这是为了给后续开发和交付留清晰边界。
- 如果主人后续要完全替换 UI 左上角品牌、文档命名、仓库名和公开说明，可以单独作为品牌清理阶段处理。

优先顺序：

1. 给热点/舆情 feed 增加“分析此条”动作，按 `5.4 mini -> 5.4 -> 5.5` 分层生成摘要、风险、机会和行动建议。
2. 把舆情分析结果写入 Obsidian `00-Inbox/needs-review`，并通过做梦流程整理重复和垃圾记忆。
3. 观察浏览器 TTS 的实际稳定性；只有在音质或跨设备一致性不足时，再升级云端 TTS。
4. 等核心闭环稳定后，再做飞书公司管理 MVP。

## 10. 2026-06-07 飞书聊天回调修复记录

主人反馈：飞书应用已经配置好，但在飞书里发消息“没有反应”。

排查结论：

- 飞书应用侧已经能显示“沫汐 机器人”，说明机器人创建和基础展示没有问题。
- BaiLongma 后端服务是 active，`https://bairui.chat/health` 正常。
- 飞书 App ID、App Secret、Verification Token 在服务等价环境下可读取。
- App ID + App Secret 可以向飞书开放平台成功换取 tenant access token。
- 后端本地 `/social/feishu/webhook` challenge 握手可返回 200。
- 真正阻断点在 Nginx：`bairui.chat` 全站开启了 Basic Auth，飞书回调不会带网页登录账号密码，所以公网 webhook 被拦成 401，事件进不了后端。

已完成修复：

- 在 Nginx 中为 `location = /social/feishu/webhook` 单独关闭 Basic Auth。
- 该路径继续反代到 `127.0.0.1:3721`，不放开整个站点。
- 修复后重新加载 Nginx，配置检查通过。
- 后端社交配置读取逻辑已补强：社交模块读取环境变量失败时，会从持久化 social 配置读取，避免网页设置保存后重启丢失读取源。

验证结果：

- 公网错误 token 请求返回 `403 invalid token`，不再是 `401 Authorization Required`。
- 公网正确 challenge 请求返回 `200`，并返回 challenge body。
- 飞书 tenant token API 检查返回 `code: 0`，说明 App ID/Secret 有效。
- 模拟 `im.message.receive_v1` 飞书消息事件可以进入后端并写入 `FEISHU` 会话。
- 后端会尝试按 `feishu:open_id:<id>` 回复；模拟测试使用的是假 open_id，所以飞书发送 API 返回“open_id 不存在”，这是预期失败，不代表真实用户链路失败。

当前边界：

- 当前已打通“飞书聊天机器人回调”基础链路。
- 还需要主人在飞书开放平台确认事件订阅 URL 为 `https://bairui.chat/social/feishu/webhook`，并订阅 `im.message.receive_v1`。
- 当前已支持飞书事件加密；Encrypt Key 已存入服务器运行配置，后端可以解密飞书加密 challenge 并返回 challenge。
- 飞书公司管理 MVP 尚未完成；现在只是聊天收发基础能力，不代表审批、日程、文档、公司管理自动化已经可用。

追加排查：

- 主人 19:54 在飞书给机器人发送“你好”后，服务器 Nginx 访问日志没有出现来自飞书开放平台的 `/social/feishu` 或 `/social/feishu/webhook` 请求。
- 因此当时的“没反应”不是后端已收到但没回复，而是飞书平台没有把该消息事件推送到服务器。
- 后端已兼容飞书 v2 事件体的 `header.token`，避免平台真正推送 v2 事件后被旧的 `body.token` 校验逻辑误拒绝。
- Nginx 已增加 `/social/feishu` 旧路径 alias，两个公网路径都可通过 challenge：
  - `https://bairui.chat/social/feishu/webhook`
  - `https://bairui.chat/social/feishu`
- 已删除此前用于烟测的 `feishu:open_id:ou_codex_synthetic` 模拟记录，避免 Brain UI 中继续显示测试乱码。

飞书平台侧待确认：

- 机器人能力已开启。
- 事件订阅方式使用“将事件发送至开发者服务器”，请求地址填上面任一已验证路径。
- 消息与群组分类下订阅“接收消息 v2.0”，事件类型为 `im.message.receive_v1`。
- 单聊权限至少包含“读取用户发给机器人的单聊消息”或“获取用户发给机器人的单聊消息”；回复还需要机器人发消息权限。
- 修改权限或事件订阅后，需要在飞书开放平台发布/生效，并在目标租户安装或更新应用。
- 如果仍无请求，去飞书开放平台“日志检索 -> 事件日志检索”查看是否触发并推送该事件。

## 11. 2026-06-07 飞书公司身份识别第一阶段

主人要求：根据飞书文档继续优化机器人，让沫汐在飞书里更适合管理公司、文件和文档；当前首要问题是她分不清飞书上是谁在和她聊天。

本轮先完成“身份识别层”，不直接进入文件写入、审批、公司自动化等高风险动作。

已完成：

- 新增飞书 profile/identity 处理模块。
- 飞书入站消息会读取事件体中的 `sender.sender_id`、`message.chat_id`、`message.chat_type` 和 `message.message_id`。
- 飞书用户不再统一映射成主人 `ID:000001`。
- 每个飞书发送者会生成独立 canonical ID：`FEISHU:<open_id>`。
- 回复仍保留真实外部投递目标：`feishu:open_id:<open_id>`。
- 对话内容会增加飞书发送者上下文前缀，包含显示名、单聊/群聊、chat_id、open_id/user_id/union_id。
- 写入 `user_identities`，把 `FEISHU + external_id` 绑定到独立 canonical ID。
- 写入 `entities` label，用于后续在 UI、记忆和公司上下文中识别人。
- 后端会尝试通过飞书通讯录接口获取用户显示名；没有权限或失败时退回 open_id 摘要，不阻塞聊天。
- 微信仍保留主人单用户模式，避免个人陪伴链路被飞书公司多人模式影响。

验证结果：

- 本地身份烟测构造 Alice/Bob 两个飞书用户，分别生成：
  - `FEISHU:ou_codex_alice_identity`
  - `FEISHU:ou_codex_bob_identity`
- `resolveCanonicalUserId` 返回各自的飞书 ID，不再回落到 `ID:000001`。
- 会话记录保留各自 `external_party_id = feishu:open_id:<open_id>`，后续回复可以路由回对应飞书用户。
- 烟测数据已清理，没有保留测试用户、测试会话或测试实体。
- 加密 challenge 复测通过：`200 {"challenge":"moxi_identity_challenge_ok"}`。

下一阶段建议：

1. 飞书真实消息接入后，确认真实 open_id、显示名、群聊 chat_id 是否正确写入。
2. 增加“谁在群里说话、谁被 @、当前群是什么项目”的群聊上下文摘要。
3. 接入飞书云文档/文件的只读能力：搜索文档、读取标题、读取正文摘要、列出最近文件。
4. 给文件和文档能力加权限边界：默认只读；写文档、改任务、发公告、审批类动作必须二次确认。
5. 最后再做公司管理工具：任务分派、会议纪要、日报周报、项目状态看板、审批提醒。

## 12. 2026-06-07 飞书整体优化评估

主人要求：参考飞书文档，整体优化飞书机器人，让沫汐在飞书里更好地管理公司、文件和协作。

本轮查阅飞书官方 Agent 集成文档后，确认飞书能力适合拆成三层：

- 凭据层：一键创建飞书应用，用于快速获得 App ID、App Secret、常见权限和事件订阅。
- 交互层：Channel SDK 或事件回调，用于让 Agent 在单聊、群聊和评论中收发消息。
- 执行层：飞书 CLI、OpenAPI MCP 或直接 OpenAPI 适配器，用于操作文档、日历、表格、邮件和任务。

当前系统已经完成的是交互层的一部分：公网回调、加密事件、tenant token、基础收发和飞书用户身份分离。还没有完成真正公司管理需要的组织、文档、表格、任务、日历、审批和审计能力。

新增文档：

- `docs/FEISHU_COMPANY_MANAGEMENT.md`：记录飞书公司管理缺口、权限计划、F0-F6 分阶段路线和官方参考链接。

当前关键缺口：

- 真实单聊和真实群 @ 事件仍需现场验证。
- 事件幂等和快速 ACK + 异步队列还没做。
- 通讯录、部门、角色、群/项目映射还没做。
- 云文档、文件搜索、多维表格记录查询还没接。
- 任务、日程、审批只能规划，不能直接放权执行。
- 飞书卡片确认和审计日志还没做。

下一步执行顺序：

1. 验证真实飞书单聊事件。
2. 验证真实飞书群 @ 事件。
3. 增加事件幂等，避免重复事件导致重复执行。
4. 增加快速 ACK 和异步处理队列，避免飞书回调超时。
5. 接入只读通讯录/部门信息，建立公司身份图谱。
6. 接入只读云文档搜索和多维表格记录查询。
7. 生成第一份基于真实飞书数据的主人经营简报。
8. 最后再开放经卡片确认的任务、日程、表格写入和审批提醒。

安全边界：

- 第一阶段不要申请“所有群所有消息”或大范围编辑权限，优先使用单聊和群 @ 消息权限。
- 审批、HR、财务、合同、对外承诺、删除/移动文件等动作默认禁用。
- 飞书 CLI/MCP 可以用，但只能作为受控执行层，不能绕过权限策略和主人确认。
