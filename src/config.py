import os
import logging
from dotenv import load_dotenv
import streamlit as st

logger = logging.getLogger(__name__)

load_dotenv()

def load_secret(key: str, default: str = None) -> str:
    """Load secret from .env (local) or st.secrets (Streamlit Cloud), with fallback."""
    # Try st.secrets first (Streamlit Cloud)
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        # st.secrets not available (local dev), continue to .env
        pass
    
    # Fall back to .env / environment variables
    value = os.getenv(key, default)
    if value is None:
        logger.error(f"Secret '{key}' not found in environment or st.secrets")
    return value


# LLM Configuration
GROQ_API_KEY = load_secret("GROQ_API_KEY")

# Tavily Search Configuration
TAVILY_API_KEY = load_secret("TAVILY_API_KEY")

# LangSmith Configuration (optional, for tracing)
LANGCHAIN_API_KEY = load_secret("LANGCHAIN_API_KEY", default="")
LANGCHAIN_PROJECT = load_secret("LANGCHAIN_PROJECT", default="ai-news-briefing")
LANGCHAIN_TRACING_V2 = load_secret("LANGCHAIN_TRACING_V2", default="false").lower() == "true"

# Enable LangSmith tracing if API key is provided
if LANGCHAIN_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = LANGCHAIN_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = LANGCHAIN_PROJECT
    logger.info(f"LangSmith tracing enabled for project: {LANGCHAIN_PROJECT}")

# Topic Configuration
TOPIC_PRESETS = ["Artificial Intelligence", "Technology", "Economics"]
CUSTOM_TOPIC_MAX_LENGTH = 200

# Stories Configuration
N_OPTIONS = [3, 5, 10]
MAX_N = 10
CANDIDATE_MULTIPLIER = 3
MIN_CANDIDATE_POOL = 15

# Time Range Configuration (Tavily time_range format)
TIME_RANGE_OPTIONS = {
    "Last 24 hours": "day",
    "Last 7 days": "week",
    "Last 30 days": "month",
}

# Summary Configuration
SUMMARY_MODES = ["Quick", "Standard"]
SUMMARY_LENGTH_INSTRUCTIONS = {
    "Quick": "Provide exactly one concise sentence summarizing the story.",
    "Standard": "Provide two to three concise sentences summarizing the story.",
}

# Search Configuration
SEARCH_TIMEOUT = 15  # seconds
SEARCH_MAX_RETRIES = 2

# LLM Configuration
LLM_MODEL = "openai/gpt-oss-120b"
LLM_TEMPERATURE = 0.2
LLM_MAX_TOKENS = 500
LLM_TIMEOUT = 30  # seconds

# Duplicate Detection Configuration
HEADLINE_SIMILARITY_THRESHOLD = 0.85

# arXiv Research Papers Configuration
ARXIV_CATEGORY_OPTIONS = {
    "AI (cs.AI)": "cs.AI",
    "Computation & Language / NLP (cs.CL)": "cs.CL",
    "Machine Learning (cs.LG)": "cs.LG",
    "Computer Vision (cs.CV)": "cs.CV",
    "Deep Learning (cs.NE)": "cs.NE",
    "Agentic AI (cs.MA)": "cs.MA",
}
ARXIV_DEFAULT_CATEGORIES = ["cs.AI", "cs.CL", "cs.LG"]
ARXIV_N_OPTIONS = [3, 5, 10]

# Auto Industry Connected Services Configuration
AUTO_OEM_GROUPS = {
    "Chinese OEMs": ["BYD", "NIO", "XPeng", "Li Auto", "Geely/Zeekr", "Xiaomi"],
    "Stellantis & Western OEMs": ["Stellantis", "Volkswagen", "Toyota", "General Motors", "Ford", "Hyundai"],
}
AUTO_QUERY_TEMPLATE = "{oem} connected car software infotainment features"
AUTO_SCORING_TOPIC = "connected vehicle software features"

# AI Product Releases Configuration
AI_COMPANIES = ["OpenAI", "Anthropic", "Google DeepMind", "Nvidia", "Meta AI", "xAI", "Mistral AI"]
AI_RELEASES_QUERY_TEMPLATE = "{company} announces new product launch"
AI_RELEASES_SCORING_TOPIC = "new AI product or model release announcement"

# Identity & Access Management / Cybersecurity Configuration
IAM_SECURITY_COMPANIES = ["Okta", "Microsoft Entra", "CyberArk", "Ping Identity", "SailPoint", "CrowdStrike", "Palo Alto Networks"]
IAM_SECURITY_QUERY_TEMPLATE = "{company} identity access management cybersecurity news"
IAM_SECURITY_SCORING_TOPIC = "identity and access management, authentication, cybersecurity threats and defenses"

# PM Voices (RSS) Configuration
PM_RSS_FEEDS = {
    "Lenny's Newsletter": "https://www.lennysnewsletter.com/feed",
    "Product Growth (Aakash Gupta)": "https://www.news.aakashg.com/feed",
    "Shreyas Doshi": "https://shreyasdoshi.substack.com/feed",
}
PM_SINCE_DAYS_OPTIONS = [3, 7, 14]
PM_DEFAULT_SINCE_DAYS = 7

logger.info("Configuration loaded successfully")
