# Chinese Report Policy

## 1. Rule

Every phase must produce a Chinese report for the owner.

Research notes, source excerpts, API documentation, code comments, and technical references may remain in English when that is more accurate or efficient. However, the phase report must be written in Chinese.

## 2. Required Report Timing

Write a Chinese report when:

- A phase is completed.
- A major architecture decision is made.
- A deployment milestone is reached.
- A risky integration is evaluated.
- A feature is ready for owner review.
- A blocker changes the plan.

## 3. Required Report Location

Reports should be stored under:

```text
reports/
```

Naming format:

```text
phase-XX-short-title.zh-CN.md
```

Examples:

```text
phase-00-architecture-plan.zh-CN.md
phase-01-hermes-vps-mvp.zh-CN.md
phase-02-feishu-company-management.zh-CN.md
```

## 4. Required Structure

Each Chinese phase report should include:

1. 阶段目标
2. 已完成内容
3. 当前效果
4. 架构或决策变化
5. 风险与边界
6. 需要主人确认的事项
7. 下一阶段计划

## 5. Style

Reports should be:

- Clear and owner-readable.
- Practical rather than academic.
- Direct about what works and what does not work yet.
- Explicit about risks.
- Specific about next actions.

## 6. Source Language

English research is acceptable. The final phase report must be Chinese.

If source material is in English, summarize the owner-facing conclusion in Chinese and keep source links in the report when useful.
