from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class BriefRequest(BaseModel):
    """User request for a news briefing."""
    topic: str = Field(..., description="News topic to search for")
    n: int = Field(5, description="Number of stories requested", ge=1, le=10)
    time_range: str = Field("Last 7 days", description="Time range for news")
    summary_mode: str = Field("Standard", description="Summary length preference")


class RawSearchResult(BaseModel):
    """Raw search result from Tavily."""
    title: str
    url: str
    publisher: Optional[str] = None
    snippet: Optional[str] = None
    date: Optional[str] = None
    entity_label: Optional[str] = None  # e.g. OEM/company name for multi-query searches


class StoryCandidate(BaseModel):
    """Processed story candidate after normalization and scoring."""
    story_id: str = Field(..., description="Unique identifier for the story")
    headline: str
    url: str
    publisher: Optional[str] = None
    snippet: Optional[str] = None
    published_at: Optional[str] = None
    relevance_score: float = Field(0.0, ge=0.0, le=1.0)
    raw_source: Optional[dict] = None  # store raw result for reference
    entity_label: Optional[str] = None  # e.g. OEM/company name for multi-query searches


class StoryResult(BaseModel):
    """Final summarized story result."""
    story_id: str
    headline: str
    summary: str
    publisher: Optional[str] = None
    published_at: Optional[str] = None
    source_url: str
    content_limitations: Optional[str] = None
    entity_label: Optional[str] = None  # e.g. OEM/company name for multi-query searches


class BriefResponse(BaseModel):
    """Final response containing the news briefing."""
    stories: List[StoryResult]
    requested_n: int
    returned_n: int
    effective_topic: str
    time_range_label: str
    summary_mode: str
    partial_notice: Optional[str] = None
    error: Optional[str] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class SearchError(Exception):
    """Custom exception for search provider failures."""
    pass


# --- Research Papers (arXiv) models ---

class ArxivPaper(BaseModel):
    """A single paper fetched from the arXiv API."""
    paper_id: str
    title: str
    authors: List[str]
    abstract: str
    pdf_url: str
    entry_url: str
    published: str
    primary_category: str


class PaperExplanation(BaseModel):
    """Plain-language, section-by-section explanation of a paper's abstract."""
    problem: str
    approach: str
    key_results: str
    why_it_matters: str
    limitations: str


class PaperBriefResult(BaseModel):
    """A paper paired with its plain-language explanation."""
    paper: ArxivPaper
    explanation: Optional[PaperExplanation] = None


class PaperBriefResponse(BaseModel):
    """Final response containing the research paper briefing."""
    results: List[PaperBriefResult]
    requested_n: int
    returned_n: int
    categories: List[str]
    partial_notice: Optional[str] = None
    error: Optional[str] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# --- PM Voices (RSS) models ---

class RssEntry(BaseModel):
    """A single entry fetched from an RSS/Atom feed."""
    source_name: str
    title: str
    link: str
    published: Optional[str] = None
    description: Optional[str] = None


class PmUpdateResult(BaseModel):
    """An RSS entry paired with its grounded summary."""
    entry: RssEntry
    summary: Optional[str] = None


class PmBriefResponse(BaseModel):
    """Final response containing the PM voices briefing."""
    results: List[PmUpdateResult]
    feed_names: List[str]
    since_days: int
    error: Optional[str] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)
