from dataclasses import dataclass
import os

@dataclass(frozen=True)
class Settings:
    db_path: str = os.getenv("SCHOLARPLAN_DB", "scholarplan.db")
    provider: str = os.getenv("SCHOLARPLAN_PROVIDER", "mock")
    max_steps: int = int(os.getenv("SCHOLARPLAN_MAX_STEPS", "20"))
    max_replans: int = int(os.getenv("SCHOLARPLAN_MAX_REPLANS", "3"))
    dedup_similarity_threshold: float = float(os.getenv("SCHOLARPLAN_DEDUP_THRESHOLD", "0.90"))
    max_sources_per_task: int = int(os.getenv("SCHOLARPLAN_MAX_SOURCES_PER_TASK", "5"))
    min_source_relevance: float = float(os.getenv("SCHOLARPLAN_MIN_RELEVANCE", "0.25"))
    request_timeout_seconds: int = int(os.getenv("SCHOLARPLAN_REQUEST_TIMEOUT", "20"))

    # Measurable evaluation targets added in response to Unit 6 feedback.
    target_valid_plan_rate: float = 0.95
    target_retrieval_success: float = 0.90
    target_critic_precision: float = 0.85
    target_critic_recall: float = 0.80
    target_unsupported_output_rate: float = 0.05
    target_e2e_success: float = 0.90
