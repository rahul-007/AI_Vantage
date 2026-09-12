import logging
from langchain_groq import ChatGroq

from src.config import GROQ_API_KEY, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS, LLM_TIMEOUT

logger = logging.getLogger(__name__)


def get_llm_client(structured_output_schema=None):
    """Build a configured ChatGroq client, optionally wrapped with structured output."""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not configured. Please set it in environment or st.secrets.")

    logger.info(f"Initializing LLM: model={LLM_MODEL}, temperature={LLM_TEMPERATURE}")

    llm = ChatGroq(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        max_tokens=LLM_MAX_TOKENS,
        timeout=LLM_TIMEOUT,
        api_key=GROQ_API_KEY,
    )

    if structured_output_schema is not None:
        return llm.with_structured_output(structured_output_schema)
    return llm
