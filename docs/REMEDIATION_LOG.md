# Remediation Log

## 1. Local LLM structured-output failures
During development, Qwen2.5-3B-Instruct occasionally returned malformed JSON or a root list instead of the requested object. The LM Studio provider now requests JSON mode, accepts object/list variants, applies `json-repair`, performs one controlled repair retry, and conservatively rejects unparseable Critic output.

## 2. Planner schema omissions
The local model occasionally omitted the required `description` field. The Planner now normalises alternative fields (`task`, `objective`, `instruction`, `title`) and applies a bounded fallback research plan when required fields are missing.

## 3. Retrieval relevance
The original retriever deduplicated sources but preserved API order, allowing some technically matched but off-topic records into the top-k set. The final retriever computes a transparent lexical relevance score from the research query, title and abstract, ranks candidates before top-k selection, and applies a default relevance gate of 0.25. The Archivist applies the same gate before publication so a claim must be both evidence-supported and relevant to the user's goal.

## 4. Execution trace final status
Earlier traces were exported before the run status was changed from `running` to `completed`. The final orchestration marks the run completed before export, and the Archivist records its own message/event before taking the final trace snapshot. Consequently `execution_trace.json` now captures the completed lifecycle state and archival action.
