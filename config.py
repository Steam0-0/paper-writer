import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class LLMConfig:
    base_url: str = os.getenv("LLM_BASE_URL", "http://localhost:8081/v1")
    api_key: str = os.getenv("LLM_API_KEY", "00000000")
    model: str = os.getenv("LLM_MODEL", "qwen-local")
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    max_retries: int = int(os.getenv("LLM_MAX_RETRIES", "3"))
    timeout: int = int(os.getenv("LLM_TIMEOUT", "60"))


@dataclass
class GraphConfig:
    recursion_limit: int = int(os.getenv("GRAPH_RECURSION_LIMIT", "20"))
    checkpoint_interval: int = int(os.getenv("GRAPH_CHECKPOINT_INTERVAL", "5"))


@dataclass
class ReviewConfig:
    min_approval_score: float = float(os.getenv("REVIEW_MIN_APPROVAL_SCORE", "0.7"))
    max_revision_cycles: int = int(os.getenv("REVIEW_MAX_REVISION_CYCLES", "3"))


@dataclass
class OutputConfig:
    format: str = os.getenv("OUTPUT_FORMAT", "docx")
    output_dir: str = os.getenv("OUTPUT_DIR", "./output")


llm_config = LLMConfig()
graph_config = GraphConfig()
review_config = ReviewConfig()
output_config = OutputConfig()