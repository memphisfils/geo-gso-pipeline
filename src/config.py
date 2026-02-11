"""
Configuration module for the GEO/GSO Pipeline.
Loads environment variables and exposes project-wide constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# ── LLM Configuration ──────────────────────────────────────────────
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")

LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o")
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")

REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "90"))
MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))

# ── Anti-Duplication ───────────────────────────────────────────────
SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.85"))
EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

# ── Article Structure Requirements ─────────────────────────────────
MIN_H2_SECTIONS: int = 4
MIN_FAQ_QUESTIONS: int = 5
MIN_SOURCES: int = 3
META_DESC_MIN: int = 150
META_DESC_MAX: int = 160
MAX_INTRO_LINES: int = 5
MIN_TAKEAWAYS: int = 5
MAX_TAKEAWAYS: int = 8

# ── Scoring Weights (each out of 20, total /100) ──────────────────
SCORE_WEIGHTS = {
    "structure": 20,
    "readability": 20,
    "sources": 20,
    "llm_friendliness": 20,
    "duplication": 20,
}

# ── Output Directories ────────────────────────────────────────────
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "out"

def validate_config() -> list[str]:
    """Validate that all required configuration is present. Returns list of errors."""
    errors = []
    if not OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY is not set. Please configure it in your .env file.")
    return errors
