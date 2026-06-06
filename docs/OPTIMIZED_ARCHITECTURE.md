# Optimized Architecture

## 1. Target Shape

The system should be optimized around three clear planes:

```text
Company Management Plane
  Feishu
  tasks, tables, docs, approvals, calendar, meetings

Personal Companion Plane
  WeChat / BaiLongma
  check-ins, reminders, quick capture, personal summaries

  Backend Intelligence Plane
  Hermes
  external-project search, API-first vision/video, research, automation, memory write-back
```

This separation prevents one chat interface from controlling everything. It also makes the system easier to secure, audit, and expand.

The planes should be built iteratively. Do not deploy all planes at once. Start with the backend runtime and Feishu company surface, then add governed Obsidian memory, then API intelligence, then personal companionship and simulations.

## 2. Core Decision

Feishu should be the first production surface.

Reason:

- It supports company workflows better than WeChat.
- It has official app and bot APIs.
- It can hold structured company data.
- It can support approvals and audit trails.
- It is better for teams, tasks, meetings, and documents.

WeChat should be added later as a personal and lightweight channel.

## 3. Optimized System Diagram

```text
Owner
  |
  +--> Feishu company bot
  |      |
  |      +--> projects
  |      +--> customers
  |      +--> sales pipeline
  |      +--> receivables
  |      +--> tasks
  |      +--> reports
  |      +--> approvals
  |
  +--> WeChat / BaiLongma
  |      |
  |      +--> personal check-ins
  |      +--> quick capture
  |      +--> companion chat
  |      +--> lightweight alerts
  |
  +--> CLI / protected admin UI
         |
         +--> deployment
         +--> maintenance
         +--> emergency controls

All channels
  -> channel policy router
  -> approval gate
  -> Hermes orchestration
  -> APIs and tools
  -> Obsidian durable memory
  -> Feishu/WeChat summaries
```

## 4. Company Management Data Model

The first Feishu implementation should use structured tables.

### Projects

Fields:

- Project name.
- Owner.
- Status.
- Priority.
- Deadline.
- Current blocker.
- Next action.
- Last update time.

### Customers

Fields:

- Customer name.
- Contact.
- Stage.
- Next follow-up date.
- Need.
- Quote status.
- Risk.
- Last interaction.

### Sales Pipeline

Fields:

- Opportunity.
- Customer.
- Amount.
- Probability.
- Stage.
- Expected close date.
- Owner.
- Next action.

### Receivables

Fields:

- Customer.
- Amount.
- Due date.
- Status.
- Responsible person.
- Reminder count.
- Risk note.

### Daily Reports

Fields:

- Employee.
- Date.
- Completed.
- Blocked.
- Tomorrow plan.
- Needs help.
- Agent summary.

### Risk Register

Fields:

- Risk.
- Severity.
- Owner.
- Trigger.
- Mitigation.
- Status.
- Escalation date.

## 5. Company Agent Workflows

### Morning Briefing

Hermes checks:

- Tasks due today.
- Overdue tasks.
- Customers needing follow-up.
- Receivables approaching due date.
- Missing daily reports.
- Approvals waiting for owner.
- High severity risks.

Output:

- Short Feishu summary.
- Full Obsidian operating note.

### Exception Alerts

Send only when something crosses a threshold:

- High-priority task overdue.
- Receivable overdue.
- Customer follow-up missed.
- Employee report missing repeatedly.
- Approval waits too long.
- Server or system risk.

### Evening Summary

Summarize:

- Completed work.
- Blockers.
- Delayed items.
- Tomorrow priorities.
- Owner approval queue.

### Weekly Management Report

Summarize:

- Project movement.
- Sales pipeline changes.
- Receivables risk.
- Team execution.
- Key decisions.
- Next week plan.

## 6. Personal Companion Workflows

WeChat/BaiLongma should handle:

- Morning personal check-in.
- Personal reminder.
- Idea capture.
- Voice or text note intake.
- Personal mood and workload awareness.
- Short summary of company state when requested.

It should avoid:

- Sending instructions to employees.
- Approving money.
- Changing company records without confirmation.
- Acting as the main company command channel.

## 7. Backend Intelligence Workflows

Hermes should coordinate:

- Search.
- Web crawling.
- OCR.
- Image understanding.
- Speech transcription.
- Video summary.
- Market research.
- Project research.
- Company data checks.
- Obsidian write-back.

The VPS remains lightweight. Heavy reasoning, vision, and video capabilities are API calls.

## 8. Memory Strategy

Use two memory types:

### Operational Memory

Stored in Feishu and used for active company workflows:

- Tasks.
- Project statuses.
- Customer follow-ups.
- Receivables.
- Approvals.

### Durable Reflective Memory

Stored in Obsidian:

- Daily and weekly reports.
- Decision logs.
- Lessons learned.
- Important customer context.
- Agent activity summaries.
- Simulation reports.
- Owner preferences.

Feishu is where work happens. Obsidian is where the system remembers and reviews.

## 9. Permission Strategy

Every action should be classified before execution.

| Level | Example | Default |
| --- | --- | --- |
| L0 Read | Read tasks, notes, market data | Allowed |
| L1 Draft | Draft reminder, report, document | Allowed |
| L2 Internal notify | Send reminder to owner or team | Allowed with logs |
| L3 Company record change | Update table status, create task | Allowed only for approved scopes |
| L4 Sensitive decision | Approve expense, external promise, HR action | Owner approval required |
| L5 Irreversible/high-risk | Trading, money movement, destructive server command | Disabled until separate design |

## 10. First Production Slice

Build this first:

```text
Hermes on VPS
+ Feishu company bot
+ Feishu project/customer/sales/risk tables
+ Obsidian operating reports
+ external search runtime and summarization
+ owner approval queue
+ Chinese phase report
```

Do not start with:

- WeChat personal-account automation.
- Autonomous trading.
- Full BaiLongma deployment.
- MiroFish simulations.
- Heavy local models.

## 11. Why This Is Better

This architecture is better because:

- Feishu handles company operations where structure and audit matter.
- WeChat stays personal and low-risk.
- Hermes remains the backend brain instead of becoming a public chatbox.
- Obsidian keeps long-term memory readable and portable.
- External APIs provide advanced intelligence without overloading the VPS.
- Approval gates protect money, legal, HR, and irreversible actions.
