import logging
import difflib
import uuid
from typing import List, Tuple
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta

from src.models import RawSearchResult, StoryCandidate
from src.config import HEADLINE_SIMILARITY_THRESHOLD, CANDIDATE_MULTIPLIER, MIN_CANDIDATE_POOL

logger = logging.getLogger(__name__)


def normalize_url(url: str) -> str:
    """Normalize URL by removing tracking params and lowercasing scheme/host."""
    if not url:
        return ""
    try:
        parsed = urlparse(url.lower())
        # Remove tracking parameters like utm_*, fbclid, etc.
        query_params = parse_qs(parsed.query)
        clean_params = {k: v for k, v in query_params.items() 
                       if not k.startswith(('utm_', 'fbclid', 'gclid'))}
        
        # Reconstruct URL without tracking params
        if clean_params:
            clean_query = "&".join([f"{k}={v[0]}" for k, v in clean_params.items()])
            return f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{clean_query}"
        else:
            return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    except Exception as e:
        logger.warning(f"Failed to normalize URL '{url}': {e}")
        return url.lower()


def normalize_headline(title: str) -> str:
    """Normalize headline text for comparison."""
    if not title:
        return ""
    return title.lower().strip()


def is_duplicate(candidate_a: StoryCandidate, candidate_b: StoryCandidate, 
                 similarity_threshold: float = HEADLINE_SIMILARITY_THRESHOLD) -> bool:
    """Check if two candidates are duplicates based on URL or headline similarity."""
    # Exact URL match (normalized)
    url_a = normalize_url(candidate_a.url)
    url_b = normalize_url(candidate_b.url)
    if url_a and url_b and url_a == url_b:
        logger.debug(f"Exact URL match: {url_a[:60]}...")
        return True
    
    # Headline similarity
    headline_a = normalize_headline(candidate_a.headline)
    headline_b = normalize_headline(candidate_b.headline)
    
    if headline_a and headline_b:
        similarity = difflib.SequenceMatcher(None, headline_a, headline_b).ratio()
        if similarity > similarity_threshold:
            logger.debug(f"Headline similarity {similarity:.2f} > {similarity_threshold}: duplicates detected")
            return True
    
    return False


def dedupe(candidates: List[StoryCandidate]) -> List[StoryCandidate]:
    """Remove duplicate candidates, keeping first occurrence."""
    logger.info(f"Starting deduplication: {len(candidates)} candidates")
    
    unique_candidates = []
    duplicates_removed = 0
    
    for candidate in candidates:
        is_dup = False
        for unique in unique_candidates:
            if is_duplicate(candidate, unique):
                is_dup = True
                duplicates_removed += 1
                break
        
        if not is_dup:
            unique_candidates.append(candidate)
    
    logger.info(f"Deduplication complete: {len(unique_candidates)} unique, {duplicates_removed} duplicates removed")
    return unique_candidates


def score_relevance(candidate: StoryCandidate, topic: str, time_range: str = "Last 7 days") -> float:
    """
    Score relevance of a candidate story based on heuristics.
    
    Returns a score between 0.0 and 1.0
    """
    score = 0.5  # base score
    
    # Keyword overlap in title and snippet
    topic_terms = set(term.lower() for term in topic.split() if len(term) > 2)
    title_terms = set(term.lower() for term in candidate.headline.split() if len(term) > 2)
    snippet_terms = set(term.lower() for term in (candidate.snippet or "").split() if len(term) > 2)
    
    title_overlap = len(topic_terms & title_terms) / len(topic_terms) if topic_terms else 0
    snippet_overlap = len(topic_terms & snippet_terms) / len(topic_terms) if topic_terms else 0
    
    score += (title_overlap * 0.3)  # title match weight
    score += (snippet_overlap * 0.15)  # snippet match weight
    
    # Presence of required fields
    if candidate.publisher:
        score += 0.1
    if candidate.snippet:
        score += 0.1
    if candidate.published_at:
        score += 0.05
    
    # Recency bonus
    if candidate.published_at:
        try:
            # Try to parse date (handles various formats)
            pub_date = None
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]:
                try:
                    pub_date = datetime.strptime(candidate.published_at, fmt)
                    break
                except:
                    continue
            
            if pub_date:
                days_old = (datetime.utcnow() - pub_date).days
                # Recent articles get bonus: max 0.1 for <24h, decreasing over time
                if days_old <= 1:
                    score += 0.1
                elif days_old <= 7:
                    score += 0.05
        except Exception as e:
            logger.debug(f"Could not parse date '{candidate.published_at}': {e}")
    
    # Clamp score between 0.0 and 1.0
    score = min(max(score, 0.0), 1.0)
    
    return score


def validate_candidate(candidate: StoryCandidate) -> bool:
    """Validate that a candidate has required fields."""
    if not candidate.headline or not candidate.headline.strip():
        logger.debug("Candidate missing headline")
        return False
    if not candidate.url or not candidate.url.strip():
        logger.debug("Candidate missing URL")
        return False
    if not candidate.publisher or not candidate.publisher.strip():
        logger.debug("Candidate missing publisher")
        return False
    return True


def normalize_and_validate(raw_results: List[RawSearchResult]) -> List[StoryCandidate]:
    """Convert raw search results to validated StoryCandidate objects."""
    logger.info(f"Normalizing and validating {len(raw_results)} raw results")
    
    candidates = []
    dropped_count = 0
    
    for i, raw in enumerate(raw_results):
        try:
            candidate = StoryCandidate(
                story_id=str(uuid.uuid4()),
                headline=raw.title,
                url=raw.url,
                publisher=raw.publisher,
                snippet=raw.snippet,
                published_at=raw.date,
                relevance_score=0.0,
                raw_source=raw.dict(),
                entity_label=raw.entity_label
            )
            
            if validate_candidate(candidate):
                candidates.append(candidate)
                logger.debug(f"Result {i+1}: valid candidate created")
            else:
                dropped_count += 1
                logger.debug(f"Result {i+1}: dropped due to missing required fields")
        except Exception as e:
            logger.warning(f"Failed to create candidate from result {i+1}: {e}")
            dropped_count += 1
    
    logger.info(f"After validation: {len(candidates)} valid, {dropped_count} dropped")
    return candidates


def select_candidates(candidates: List[StoryCandidate], n: int, topic: str, 
                     time_range: str = "Last 7 days") -> Tuple[List[StoryCandidate], str]:
    """
    Select top N candidates by relevance score.
    
    Returns:
        Tuple of (selected candidates, partial_notice message if fewer than N)
    """
    logger.info(f"Selecting top {n} from {len(candidates)} candidates")
    
    # Score all candidates
    for candidate in candidates:
        candidate.relevance_score = score_relevance(candidate, topic, time_range)
    
    # Sort by relevance score
    sorted_candidates = sorted(candidates, key=lambda c: c.relevance_score, reverse=True)
    
    # Select top N
    selected = sorted_candidates[:n]
    
    partial_notice = None
    if len(selected) < n:
        partial_notice = (
            f"We found {len(selected)} sufficiently relevant and accessible stories for this topic, "
            f"so the brief contains {len(selected)} instead of {n}."
        )
        logger.info(f"Fewer results available: {len(selected)} < {n}")
    
    logger.info(f"Selected {len(selected)} candidates (scores: {[f'{c.relevance_score:.2f}' for c in selected]})")
    
    return selected, partial_notice


def process_search_results(raw_results: List[RawSearchResult], n: int, topic: str,
                          time_range: str = "Last 7 days") -> Tuple[List[StoryCandidate], str]:
    """
    Full processing pipeline: normalize -> validate -> dedupe -> score -> select.
    
    Returns:
        Tuple of (selected candidates, partial_notice)
    """
    logger.info(f"Starting processing pipeline for topic='{topic}'")
    
    # Step 1: Normalize and validate
    candidates = normalize_and_validate(raw_results)
    
    # Step 2: Deduplicate
    candidates = dedupe(candidates)
    
    # Step 3: Select top candidates
    selected, partial_notice = select_candidates(candidates, n, topic, time_range)
    
    logger.info(f"Processing complete: {len(selected)} stories selected")
    return selected, partial_notice
