# ScholarPlan

**ScholarPlan: An LLM-Powered Planning Agent for Academic Research and Information Gathering**

ScholarPlan is a modular multi-agent research assistant. It accepts a research
goal, decomposes it into subtasks, retrieves scholarly evidence, extracts
source-grounded claims, independently verifies those claims, and archives the
accepted output with a BibTeX bibliography and execution trace.

## Architecture

The implementation follows the Unit 6 design:

* Planner
* Retriever
* Processor
* Critic
* Archivist
* SQLite3 shared blackboard

Agents exchange artefacts through the blackboard rather than invoking one
another directly. The blackboard also records KQML-inspired `request`, `inform`,
`confirm` and `reject` messages.

## Improvements implemented from Unit 6 feedback

1. Added a static UML Class Diagram in `docs/class\_diagram.md`.
2. Added measurable targets:

   * valid plan rate >= 95%
   * retrieval success >= 90%
   * deduplication threshold = 0.90
   * Critic precision >= 0.85
   * Critic recall >= 0.80
   * unsupported output rate < 5%
   * end-to-end success >= 90%
3. Added a bounded fallback: a subtask is re-planned at most three times and is
then marked `unresolvable`.

## Installation

Python 3.11+:

```bash
python -m venv .venv
```

Windows:

```bash
.venv\\Scripts\\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install:

```bash
pip install -r requirements.txt
pip install -e .
```

## Reproducible demo

```bash
python -m scholarplan.main "How can LLM agents reduce hallucinations in academic research?" --mode fixture --provider mock
```

The deterministic demo uses local fixture data and the same orchestration
interfaces as the live version. This makes testing repeatable and avoids spending
API credit during unit/functional tests.

Outputs:

* `outputs/report.md`
* `outputs/bibliography.bib`
* `outputs/execution\_trace.json`

## Live scholarly retrieval

```bash
python -m scholarplan.main "What techniques reduce hallucination in LLM-based academic research agents?" --mode live --provider lmstudio --db scholarplan_full_live.db --output outputs_full_live
```
This is the configuration used for the final live demonstration. It uses Qwen2.5-3B-Instruct through LM Studio together with live retrieval from OpenAlex, Crossref and arXiv.

## Live Azure LLM mode

Set the variables in `.env.example` in your environment, then:

```bash
python -m scholarplan.main "What techniques reduce hallucination in LLM agents?" --mode live --provider azure
```

Secrets are loaded from environment variables and must not be committed to GitHub.



## Free local LLM mode with LM Studio

ScholarPlan also supports a real local LLM through LM Studio without Azure or a
paid API. The tested configuration is:

```text
Base URL: http://localhost:1234/v1
Model: qwen2.5-3b-instruct
```

PowerShell:

```powershell
$env:LM\_STUDIO\_BASE\_URL="http://localhost:1234/v1"
$env:LM\_STUDIO\_MODEL="qwen2.5-3b-instruct"
$env:LM\_STUDIO\_API\_KEY="lm-studio"

python -m scholarplan.main "What techniques reduce hallucination in LLM-based academic research agents?" --mode fixture --provider lmstudio --db scholarplan\_live.db --output outputs\_live
```

After that succeeds, use `--mode live` to retrieve from OpenAlex, Crossref and
arXiv as well. Full instructions are in `docs/LM\_STUDIO\_LIVE\_RUN.md`.



## Testing

```bash
pytest -q
```

The current suite includes:

* Blackboard persistence
* Planner schema behaviour
* DOI deduplication
* Critic supported/unsupported decisions
* End-to-end fixture execution
* Three-attempt re-planning fallback

Run the Critic evaluation harness with:

```bash
python evaluation/run\_evaluation.py
```

## Key implementation decisions

* **Plain Python orchestration** keeps the assessed control loop visible instead
of obscuring it behind a framework.
* **SQLite blackboard** makes state persistent, inspectable and transaction-safe.
* **Independent Critic** separates claim generation from verification.
* **Bounded ReAct-style replanning** prevents runaway loops and controls cost.
* **Deterministic test provider** isolates orchestration/testing from
non-deterministic LLM behaviour.
* **DOI/arXiv ID + title-similarity deduplication** prevents repeated sources
from inflating evidence.
* **Relevance ranking and publication gate** rank sources against the research goal
before top-k selection and prevent off-topic verified claims from entering the report.

## Limitations

* The mock provider is for deterministic testing, not a substitute for the final
LLM demonstration.
* Crossref often provides metadata without abstracts.
* Relevance ranking is a transparent lexical baseline; future work should replace
it with Sentence-BERT embeddings as proposed in Unit 6.
* LLM-based verification can still produce false positives/negatives; therefore
Critic precision/recall must be reported.
* The baseline is single-user and single-machine, consistent with the original
proposal assumptions.

## Academic integrity and sources

The implementation is based on the literature and design choices documented in
the Unit 6 proposal, including work on ReAct, Reflexion, RAG, hallucination,
blackboard architectures, Sentence-BERT and independent verification. External
libraries, models and APIs should be acknowledged in the final submission.



## Final live demonstration evidence

The submitted evidence includes a successful live run using:

* **LLM:** Qwen2.5-3B-Instruct through LM Studio (`http://localhost:1234/v1`)
* **Retrieval:** OpenAlex, Crossref and arXiv
* **Observed run:** 3 tasks, 15 retrieved records, 12 evidence-verified claims
* **Testing:** 7/7 tests passed, including the three-attempt re-planning cap

The final code additionally includes a relevance-ranking remediation so verified but off-topic records are filtered before publication. See `docs/REMEDIATION\_LOG.md`.

## External software and services

ScholarPlan uses or supports the following external components, all acknowledged here for academic integrity:

* Python 3.11+
* SQLite3 (Python standard library)
* OpenAI Python client for OpenAI-compatible local/Azure endpoints
* `json-repair` for structured-output remediation
* `pytest` for automated tests
* LM Studio local OpenAI-compatible API
* Qwen2.5-3B-Instruct (local LLM used in the final live demonstration)
* OpenAlex API
* Crossref REST API
* arXiv API

Academic design references are those documented in the Unit 6 proposal, including work on ReAct, Reflexion, retrieval-augmented generation, hallucination, blackboard architectures, Sentence-BERT and independent verification.



# Academic Basis for Design Decisions



ScholarPlan’s architecture and implementation decisions are informed by established research. The shared blackboard architecture follows the coordination principles described by Hayes-Roth (1985). The retrieval component reflects the principle of grounding language-model outputs in external evidence described by Lewis et al. (2020). The bounded planning and acting cycle is informed by ReAct (Yao et al., 2023), while the separation between LLM generation and independent verification is consistent with the LLM-Modulo perspective presented by Kambhampati et al. (2024). Hallucination risk and the need for verification are informed by Ji et al. (2023). Sentence-BERT (Reimers and Gurevych, 2019) provides the academic basis for the proposed future improvement from title-based similarity to semantic embedding-based relevance and deduplication.

# 

# Academic References



Hayes-Roth, B. (1985) ‘A blackboard architecture for control’, Artificial Intelligence, 26(3), pp. 251–321. doi: 10.1016/0004-3702(85)90063-3.



Ji, Z., Lee, N., Frieske, R., Yu, T., Su, D., Xu, Y., Ishii, E., Bang, Y.J., Madotto, A. and Fung, P. (2023) ‘Survey of hallucination in natural language generation’, ACM Computing Surveys, 55(12), Article 248, pp. 1–38. doi: 10.1145/3571730.



Kambhampati, S., Valmeekam, K., Guan, L., Verma, M., Stechly, K., Bhambri, S., Saldyt, L.P. and Murthy, A.B. (2024) ‘Position: LLMs can’t plan, but can help planning in LLM-Modulo frameworks’, Proceedings of the 41st International Conference on Machine Learning, Proceedings of Machine Learning Research, 235, pp. 22895–22907.



Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W., Rocktäschel, T., Riedel, S. and Kiela, D. (2020) ‘Retrieval-augmented generation for knowledge-intensive NLP tasks’, Advances in Neural Information Processing Systems, 33, pp. 9459–9474.



Reimers, N. and Gurevych, I. (2019) ‘Sentence-BERT: Sentence embeddings using Siamese BERT-networks’, Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing and the 9th International Joint Conference on Natural Language Processing (EMNLP-IJCNLP), Hong Kong, China: Association for Computational Linguistics, pp. 3982–3992. doi: 10.18653/v1/D19-1410.



Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K.R. and Cao, Y. (2023) ‘ReAct: Synergizing reasoning and acting in language models’, The Eleventh International Conference on Learning Representations (ICLR 2023).

