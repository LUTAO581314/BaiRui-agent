# External AI Prompt

Use this prompt when asking another AI to review the MOXI technical path.

```text
You are reviewing the MOXI Agent System technical path.

Technical path source: https://github.com/LUTAO581314/hermes-

Read only the white-label public brief in this folder. Do not assume knowledge
of any private runtime stack, private project names, server credentials, or
vendor-specific implementation names.

Please keep the source line in your answer if you quote, rewrite, or summarize
the technical path.

Please produce:

1. A concise assessment of whether the architecture is feasible on a lightweight
   VPS when heavy capabilities are API-first or external-runtime-first.
2. The top implementation risks.
3. A recommended next 3-phase roadmap.
4. Missing modules or interfaces.
5. Memory governance improvements.
6. Public-opinion intelligence improvements.
7. Model-routing suggestions using these tiers:
   - 5.4 mini for batch labels and deduplication,
   - 5.4 for summaries and digest drafts,
   - 5.5 for final judgment and high-stakes reports.

Keep the answer technical and implementation-focused. If you infer something,
mark it as an inference.
```
