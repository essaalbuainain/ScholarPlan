from __future__ import annotations
import json
from pathlib import Path
from scholarplan.providers.mock import MockLLMProvider
from scholarplan.config import Settings

def safe_div(a, b):
    return a / b if b else 0.0

def main():
    root = Path(__file__).resolve().parents[1]
    gold = json.loads((root / "evaluation" / "critic_gold.json").read_text(encoding="utf-8"))
    provider = MockLLMProvider()

    tp = fp = fn = tn = 0
    cases = []
    for item in gold:
        pred = provider.verify_claim(item["claim"], item["evidence"])["label"]
        actual = item["gold"]
        cases.append({"gold": actual, "predicted": pred, "claim": item["claim"]})
        if actual == "SUPPORTED" and pred == "SUPPORTED": tp += 1
        elif actual == "UNSUPPORTED" and pred == "SUPPORTED": fp += 1
        elif actual == "SUPPORTED" and pred == "UNSUPPORTED": fn += 1
        else: tn += 1

    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, tp + fn)
    settings = Settings()

    result = {
        "critic_precision": round(precision, 3),
        "critic_recall": round(recall, 3),
        "target_precision": settings.target_critic_precision,
        "target_recall": settings.target_critic_recall,
        "precision_pass": precision >= settings.target_critic_precision,
        "recall_pass": recall >= settings.target_critic_recall,
        "cases": cases,
    }
    out = root / "evidence" / "evaluation_results.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
