from langchain_groq import ChatGroq
import os
from typing import Optional

from config import (
    GROQ_MODEL_NAME,
    GROQ_TEMPERATURE,
    GROQ_MAX_TOKENS
)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, will rely on system environment variables


def get_llm(max_tokens: Optional[int] = None) -> ChatGroq:
    """
    Returns a configured ChatGroq LLM instance.
    This function should be the ONLY place where the LLM is initialized.
    
    Args:
        max_tokens: Optional override for max_tokens (defaults to GROQ_MAX_TOKENS)
    """
    # Check if API key is set
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY environment variable is not set. "
            "Please set it before running the application. "
            "You can set it by running: export GROQ_API_KEY='your-api-key' "
            "or by creating a .env file with GROQ_API_KEY=your-api-key"
        )

    # Use provided max_tokens or fall back to config
    token_limit = max_tokens if max_tokens is not None else GROQ_MAX_TOKENS

    return ChatGroq(
        model=GROQ_MODEL_NAME,
        temperature=GROQ_TEMPERATURE,
        max_tokens=token_limit,
        groq_api_key=api_key,
    )
