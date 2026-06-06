# Roadmap

## Phase 0: Plan and Repository

Goal: turn the empty repository into the control center for the system.

Tasks:

- Add master plan.
- Add architecture.
- Add risk guardrails.
- Add implementation roadmap.
- Push to GitHub.

Exit criteria:

- Repository clearly explains the intended system.
- Next engineer or agent can continue from the docs.

## Phase 1: Hermes VPS MVP

Goal: deploy Hermes safely on the VPS.

Tasks:

- Install Docker and Docker Compose plugin.
- Create `hermes` Linux user.
- Create `/opt/hermes-system`.
- Add `docker-compose.yml`.
- Add `.env.example`.
- Configure model provider.
- Configure search and multimodal API provider placeholders.
- Start Hermes.
- Add health check.
- Document start/stop/update commands.

Exit criteria:

- Hermes runs on the VPS.
- It can complete one safe command or research task.
- Logs are visible.

## Phase 2: Obsidian Memory MVP

Goal: make Obsidian the durable memory base.

Tasks:

- Create vault structure.
- Add note templates.
- Add daily report template.
- Add decision log template.
- Add market watch template.
- Define file naming conventions.
- Add Hermes write-back process.

Exit criteria:

- Hermes can write a report into the vault.
- The owner can read and edit the result directly.

## Phase 3: Feishu MVP

Goal: add a stable messaging channel before WeChat.

Tasks:

- Create Feishu app.
- Configure event subscription.
- Build or deploy callback adapter.
- Add command parser.
- Add daily briefing push.
- Add manual approval response pattern.

Exit criteria:

- Owner can ask for a summary from Feishu.
- System can push one daily briefing.
- Sensitive actions require approval.

## Phase 4: Research and Market Watch

Goal: create a useful research pipeline without trading.

Tasks:

- Create watchlist.
- Add market data source.
- Add news source.
- Add source citation convention.
- Add bull/bear/risk analysis template.
- Add daily market note generation.
- Add Feishu summary.

Exit criteria:

- A daily market brief is generated.
- Output is research-only.
- No broker or trading API is connected.

## Phase 4.5: Search and Multimodal API Layer

Goal: let the system search, read images, transcribe speech, and summarize videos through APIs while keeping the VPS lightweight.

Tasks:

- Add search API adapter.
- Add web crawling/extraction API adapter.
- Add OCR API adapter.
- Add image understanding API adapter.
- Add speech transcription API adapter.
- Add video summary workflow.
- Add cost and rate-limit controls.
- Add Obsidian templates for image/video/web analysis.

Exit criteria:

- Hermes can call one search provider.
- Hermes can analyze one image through an API.
- Hermes can transcribe or summarize one video through an API workflow.
- Results are written to Obsidian.
- No heavy local model is required on the VPS.

## Phase 5: BaiLongma Interaction Layer

Goal: add Chinese persona and richer interaction.

Tasks:

- Deploy BaiLongma or create adapter.
- Decide whether it routes to Hermes or shares memory files.
- Configure Feishu integration.
- Evaluate WeChat bridge separately.
- Add Brain UI access boundary.

Exit criteria:

- Owner can interact in Chinese through BaiLongma.
- Important results still write back to Obsidian.

## Phase 6: MiroFish Simulation Lab

Goal: add structured multi-agent simulation.

Tasks:

- Deploy MiroFish.
- Create simulation brief template.
- Build Obsidian export process.
- Build report import process.
- Test one project decision simulation.
- Test one market scenario simulation.

Exit criteria:

- A simulation can start from Obsidian context.
- The final report returns to Obsidian.

## Phase 7: WeChat Bridge Review

Goal: support WeChat only within acceptable risk boundaries.

Tasks:

- Prefer official channels where possible.
- Review personal-account automation risks.
- Avoid bypassing platform restrictions.
- Add rate limits.
- Add manual confirmation.
- Keep sensitive commands disabled.

Exit criteria:

- WeChat route is documented.
- Owner understands trade-offs.
- No high-risk automation is enabled by default.

## Phase 8: Operations Hardening

Goal: make the system maintainable.

Tasks:

- Add backup script.
- Add restore runbook.
- Add log rotation.
- Add service update command.
- Add health monitor.
- Add alerting.
- Add secret rotation notes.

Exit criteria:

- System can be recovered from backup.
- Services can be updated without guesswork.

## Phase 9: Optional Execution Integrations

Goal: evaluate whether any real-world action APIs should be connected.

Examples:

- Broker API.
- Cloud provider API.
- GitHub write operations.
- Deployment automation.

Required before enabling:

- Separate threat model.
- Approval flow.
- Spending or position limits.
- Full audit log.
- Kill switch.
- Dry-run mode.

Exit criteria:

- No irreversible action is enabled without a written safety design.
