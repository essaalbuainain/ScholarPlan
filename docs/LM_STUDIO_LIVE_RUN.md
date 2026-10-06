# ScholarPlan Live Run with LM Studio

## Confirmed local configuration

```text
Base URL: http://localhost:1234/v1
Model ID: qwen2.5-3b-instruct
```

## 1. Keep LM Studio running

In LM Studio open **Local Model API** and leave the server as **Running**.

## 2. Open PowerShell in the extracted project folder

```powershell
cd "C:\path\to\ScholarPlan"
```

## 3. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If activation is blocked for the current PowerShell session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 4. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

## 5. Set LM Studio environment variables

```powershell
$env:LM_STUDIO_BASE_URL="http://localhost:1234/v1"
$env:LM_STUDIO_MODEL="qwen2.5-3b-instruct"
$env:LM_STUDIO_API_KEY="lm-studio"
```

## 6. First real-LLM run

Start with deterministic fixture research sources so the first check isolates the
LLM integration:

```powershell
python -m scholarplan.main "What techniques reduce hallucination in LLM-based academic research agents?" --mode fixture --provider lmstudio --db scholarplan_live.db --output outputs_live
```

This is a **real LLM execution**: the Planner, Processor and Critic use
Qwen2.5-3B-Instruct through LM Studio. Fixture mode only fixes the retrieved source
set so the first integration test is reproducible.

## 7. Full live run

After the first command succeeds:

```powershell
python -m scholarplan.main "What techniques reduce hallucination in LLM-based academic research agents?" --mode live --provider lmstudio --db scholarplan_live2.db --output outputs_live2
```

This combines the local LLM with OpenAlex, Crossref and arXiv retrieval.

## Evidence screenshots to capture later

1. LM Studio API page showing **Running**
2. Successful ScholarPlan real-LLM PowerShell run
3. `pytest -q` result
4. `outputs_live/report.md`
5. selected content from `outputs_live/execution_trace.json`

## v0.3 reliability update

The LM Studio provider now requests OpenAI-compatible JSON mode and performs one
controlled JSON-repair retry if Qwen returns malformed JSON. This specifically
addresses JSONDecodeError failures seen during Processor output generation.
