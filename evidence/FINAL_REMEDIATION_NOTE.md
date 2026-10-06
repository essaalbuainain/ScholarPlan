# Final Remediation Note

The `outputs_full_live/execution_trace.json` file is refreshed from the completed SQLite run and therefore records the actual live execution: 3 tasks, 15 retrieved records, 26 candidate claims, 12 evidence-accepted claims and 14 rejected claims.

After reviewing that run, a final relevance remediation was added to the codebase. The final Retriever ranks candidates against the research goal before top-k selection, and the Archivist applies the same 0.25 relevance gate before publication. To demonstrate the effect without fabricating a second LLM run, `outputs_full_live/report.md` was regenerated deterministically from the actual accepted claims in the completed live-run database. It publishes 9 of the 12 evidence-verified claims because 3 were source-supported but insufficiently relevant to the user goal.

This distinction is intentional: **evidence verification** and **goal relevance** are separate quality gates.
