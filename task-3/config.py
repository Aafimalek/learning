import os

# -------------------------
# App-level configuration
# -------------------------

APP_NAME = "Legal Case Analysis Assistant"

# -------------------------
# LLM configuration
# -------------------------

# Groq model choices (examples):
# - "llama-3.1-70b-versatile"
# - "llama-3.1-8b-instant"
GROQ_MODEL_NAME = os.getenv(
    "GROQ_MODEL_NAME",
    "moonshotai/kimi-k2-instruct-0905"
)

# Keep temperature low for legal reasoning
GROQ_TEMPERATURE = float(
    os.getenv("GROQ_TEMPERATURE", "0.2")
)

# Token limit safety
GROQ_MAX_TOKENS = int(
    os.getenv("GROQ_MAX_TOKENS", "2048")
)

# -------------------------
# Prompt & pipeline settings
# -------------------------

PROMPT_DIR = "prompts"

# Order matters. Do not reorder without intent.
PIPELINE_STAGES = [
    "understand_case",
    "extract_facts",
    "identify_issues",
    "generate_arguments",
    "predict_judgement"
]

# -------------------------
# Memory configuration
# -------------------------

# Streamlit session keys
MEMORY_KEY = "legal_analysis_memory"

# -------------------------
# UI configuration
# -------------------------

DEFAULT_TEXTAREA_HEIGHT = 250
MAX_FOLLOW_UP_LENGTH = 500
