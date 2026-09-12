# 📰 AI Vantage

AI Vantage is a multi-page Streamlit web app that generates concise, AI-powered news and research summaries on demand across several domains — general news, academic research, the auto industry, AI product launches, product-management thought leadership, and identity/access management & cybersecurity. Pick a topic or vertical, tune the scope, and the app searches the web (or arXiv/RSS), deduplicates similar stories, and summarizes each one using an LLM.

## Features

### 🏠 Home — General News Briefing ([app.py](app.py))
- **Topic selection** — choose from predefined presets (Artificial Intelligence, Technology, Economics) or enter a custom topic (up to 200 characters).
- **Configurable results** — control the number of stories (3, 5, or 10), the time range (last 24 hours, 7 days, or 30 days), and summary length (Quick or Standard).
- **Web search** — retrieves current news articles via [Tavily](https://tavily.com/).
- **Deduplication & scoring** — filters out near-duplicate headlines (URL match or headline similarity) and ranks candidates by keyword relevance, recency, and field completeness before summarizing.
- **AI summarization** — uses [Groq](https://groq.com/)-hosted LLMs (via LangChain) to summarize each story, with prompt-injection guardrails on retrieved content.
- **Live progress tracking** — multi-stage status updates while the brief is generated.

### 📄 Research Papers ([pages/1_Research_Papers.py](pages/1_Research_Papers.py))
- Fetches recent papers from **arXiv** across selectable categories: AI (`cs.AI`), NLP (`cs.CL`), ML (`cs.LG`), Computer Vision (`cs.CV`), Deep Learning (`cs.NE`), and Agentic AI (`cs.MA`).
- Choose how many papers to fetch (3, 5, or 10).
- Each paper card includes title, authors, publication date, category, and links to the abstract and PDF.
- **Plain-language AI explanations** for each paper, broken into: Problem, Approach, Key Results, Why It Matters, and Limitations.

### 🚗 Auto Industry ([pages/2_Auto_Industry.py](pages/2_Auto_Industry.py))
- Tracks connected-car, infotainment, and software-defined vehicle news across OEMs, grouped by:
  - **Chinese OEMs:** BYD, NIO, XPeng, Li Auto, Geely/Zeekr, Xiaomi
  - **Stellantis & Western OEMs:** Stellantis, VW, Toyota, GM, Ford, Hyundai
- Multi-entity web search (via Tavily) run per selected OEM, with results scored for relevance to connected-vehicle software topics.
- Configurable number of stories, time range, and summary mode; each story tagged with its source OEM.

### 🚀 AI Product Releases ([pages/3_AI_Product_Releases.py](pages/3_AI_Product_Releases.py))
- Tracks official AI model/product launch announcements from leading AI companies: OpenAI, Anthropic, Google DeepMind, Nvidia, Meta AI, xAI, and Mistral AI.
- Multi-entity search per company, scored against a "new AI product or model release" relevance topic.
- Configurable number of stories, time range, and summary mode; each story tagged with its source company.

### 🎙️ PM Updates ([pages/4_PM_Updates.py](pages/4_PM_Updates.py))
- Aggregates and summarizes posts from curated **product management** RSS/Atom feeds:
  - Lenny's Newsletter
  - Product Growth (Aakash Gupta)
  - Shreyas Doshi
- Configurable lookback window (3, 7, or 14 days).
- Each entry summarized in 2–3 sentences, grounded strictly in the title/description (no hallucinated content), with a direct read/listen link.

### � IAM & Cybersecurity ([pages/5_IAM.py](pages/5_IAM.py))
- Tracks identity, authentication, and cybersecurity news from leading vendors: Okta, Microsoft Entra, CyberArk, Ping Identity, SailPoint, CrowdStrike, and Palo Alto Networks.
- Multi-entity search per company, scored against an "identity and access management, authentication, cybersecurity threats and defenses" relevance topic.
- Configurable number of stories, time range, and summary mode; each story tagged with its source company.

### �🛡️ Cross-cutting capabilities
- **Prompt-injection guardrails** — LLM prompts explicitly treat retrieved web/RSS/abstract content as untrusted data.
- **Partial-failure handling** — if some stories fail to summarize, the app returns the rest with a clear partial-results notice instead of failing outright.
- **Source URL integrity** — story links always come from the original search/feed data, never from LLM output.
- **Structured logging** — every pipeline stage logs timestamped, module-tagged messages for observability.
- **Optional LangSmith tracing** — trace and inspect every LLM call end-to-end.

## Tech Stack

- [Streamlit](https://streamlit.io/) — multi-page web UI
- [LangChain](https://www.langchain.com/) + [langchain-groq](https://pypi.org/project/langchain-groq/) — LLM orchestration
- [Tavily](https://tavily.com/) — news/web search API (general news, auto industry, AI product releases, IAM & cybersecurity)
- [arxiv](https://pypi.org/project/arxiv/) — arXiv API client (research papers)
- [feedparser](https://pypi.org/project/feedparser/) — RSS/Atom feed parsing (PM updates)
- [LangSmith](https://smith.langchain.com/) — optional LLM call tracing/observability
- Python (`pydantic`, `python-dotenv`, `python-dateutil`)

## Project Structure

```
app.py                        # Streamlit entry point — Home / general news briefing
requirements.txt              # Python dependencies
pages/
  1_Research_Papers.py        # arXiv paper fetching + plain-language explanations
  2_Auto_Industry.py          # Connected-car / SDV news by OEM
  3_AI_Product_Releases.py    # AI model/product launch tracking by company
  4_PM_Updates.py             # Product-management RSS feed summaries
  5_IAM.py                    # Identity/access management & cybersecurity news by vendor
src/
  config.py                   # Configuration, secrets loading, and app constants
  logging_config.py           # Logging setup
  models.py                   # Pydantic data models (BriefRequest, StoryResult, ArxivPaper, RssEntry, etc.)
  pipeline.py                  # General/multi-query brief orchestration (search -> process -> summarize)
  search.py                    # Tavily search integration (single- and multi-entity)
  processing.py                # Deduplication, relevance scoring, candidate validation
  summarize.py                 # LLM story summarization with prompt-injection guardrails
  llm_client.py                 # Groq/LangChain LLM client configuration
  arxiv_client.py                # arXiv API client for fetching recent papers
  paper_explainer.py             # LLM-based plain-language paper explanations
  paper_pipeline.py              # Research Papers page orchestration
  auto_pipeline.py               # Auto Industry page orchestration
  releases_pipeline.py           # AI Product Releases page orchestration
  iam_pipeline.py                 # IAM & Cybersecurity page orchestration
  rss_client.py                  # RSS/Atom feed fetching and parsing
  pm_summarizer.py               # LLM-based RSS entry summarization
  pm_pipeline.py                 # PM Updates page orchestration
  ui_common.py                   # Shared Streamlit UI components (cards, headers, footers, errors)
```

## Running the App Locally

### Prerequisites

- Python 3.10+
- A [Groq API key](https://console.groq.com/keys)
- A [Tavily API key](https://app.tavily.com/)

### Setup

1. **Clone the repository**

   ```bash
   git clone <your-repo-url>
   cd AI_News
   ```

2. **Create and activate a virtual environment**

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**

   ```powershell
   pip install -r requirements.txt
   ```

4. **Configure secrets**

   Create a `.env` file in the project root with your API keys:

   ```env
   GROQ_API_KEY=your_groq_api_key_here
   TAVILY_API_KEY=your_tavily_api_key_here

   # Optional: LangSmith tracing
   LANGCHAIN_API_KEY=
   LANGCHAIN_PROJECT=ai-news-briefing
   LANGCHAIN_TRACING_V2=false
   ```

   > **Note:** Never commit your `.env` file. Add it to `.gitignore` to keep API keys out of version control.
   >
   > The Research Papers and PM Updates pages use arXiv and RSS feeds directly and do not require the Tavily key, but `GROQ_API_KEY` is required across all pages for summarization.

5. **Run the app**

   ```powershell
   streamlit run app.py
   ```

6. Open the URL shown in the terminal (typically `http://localhost:8501`) in your browser. Use the sidebar page navigation to switch between Home, Research Papers, Auto Industry, AI Product Releases, PM Updates, and IAM.

## Deploying to Streamlit Cloud

When deployed on Streamlit Cloud, secrets can be configured via `st.secrets` (Settings → Secrets) instead of a `.env` file, using the same key names (`GROQ_API_KEY`, `TAVILY_API_KEY`, `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT`, `LANGCHAIN_TRACING_V2`).
