import logging
import time
from typing import Optional

from src.models import BriefRequest, BriefResponse, SearchError
from src.config import (
    N_OPTIONS, TOPIC_PRESETS, SUMMARY_MODES,
    CUSTOM_TOPIC_MAX_LENGTH, CANDIDATE_MULTIPLIER, 
    MIN_CANDIDATE_POOL, TIME_RANGE_OPTIONS
)
from src.search import search_news, search_news_multi
from src.processing import process_search_results
from src.summarize import summarize_stories

logger = logging.getLogger(__name__)


def validate_brief_request(request: BriefRequest) -> tuple[bool, Optional[str]]:
    """
    Validate a brief request.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate topic
    if not request.topic or not request.topic.strip():
        return False, "Topic cannot be empty"
    
    if len(request.topic) > CUSTOM_TOPIC_MAX_LENGTH:
        return False, f"Topic cannot exceed {CUSTOM_TOPIC_MAX_LENGTH} characters"
    
    # Validate N
    if request.n not in N_OPTIONS:
        return False, f"Number of stories must be one of {N_OPTIONS}"
    
    # Validate time_range
    if request.time_range not in TIME_RANGE_OPTIONS:
        return False, f"Time range must be one of {list(TIME_RANGE_OPTIONS.keys())}"
    
    # Validate summary_mode
    if request.summary_mode not in SUMMARY_MODES:
        return False, f"Summary mode must be one of {SUMMARY_MODES}"
    
    return True, None


def generate_brief(request: BriefRequest) -> BriefResponse:
    """
    Generate a news briefing from a user request.
    
    Orchestrates the full pipeline:
    1. Validate input
    2. Search for news
    3. Process results (normalize, dedupe, rank)
    4. Summarize stories
    5. Return formatted brief
    
    Args:
        request: BriefRequest object
        
    Returns:
        BriefResponse with stories and metadata
    """
    start_time = time.time()
    logger.info(
        f"Generating brief: topic='{request.topic}', n={request.n}, "
        f"time_range='{request.time_range}', summary_mode='{request.summary_mode}'"
    )
    
    # Step 1: Validate request
    is_valid, error_msg = validate_brief_request(request)
    if not is_valid:
        logger.error(f"Request validation failed: {error_msg}")
        return BriefResponse(
            stories=[],
            requested_n=request.n,
            returned_n=0,
            effective_topic=request.topic,
            time_range_label=request.time_range,
            summary_mode=request.summary_mode,
            error=error_msg
        )
    
    try:
        # Step 2: Calculate candidate pool size
        candidate_pool_size = max(request.n * CANDIDATE_MULTIPLIER, MIN_CANDIDATE_POOL)
        logger.info(f"Candidate pool size: {candidate_pool_size}")
        
        # Step 3: Search for news
        logger.info("Phase: Searching for news...")
        raw_results = search_news(
            topic=request.topic,
            time_range=request.time_range,
            max_results=candidate_pool_size
        )
        
        if not raw_results:
            logger.warning(f"No search results found for topic: {request.topic}")
            return BriefResponse(
                stories=[],
                requested_n=request.n,
                returned_n=0,
                effective_topic=request.topic,
                time_range_label=request.time_range,
                summary_mode=request.summary_mode,
                error="No news found for this topic in the specified time range."
            )
        
        # Step 4: Process results
        logger.info("Phase: Processing search results...")
        selected_candidates, partial_notice = process_search_results(
            raw_results=raw_results,
            n=request.n,
            topic=request.topic,
            time_range=request.time_range
        )
        
        if not selected_candidates:
            logger.warning(f"No valid candidates after processing")
            return BriefResponse(
                stories=[],
                requested_n=request.n,
                returned_n=0,
                effective_topic=request.topic,
                time_range_label=request.time_range,
                summary_mode=request.summary_mode,
                error="No suitable news found after filtering."
            )
        
        # Step 5: Summarize stories
        logger.info("Phase: Summarizing stories...")
        story_results, failed_ids = summarize_stories(
            candidates=selected_candidates,
            summary_mode=request.summary_mode
        )
        
        # Step 6: Build response
        elapsed_time = time.time() - start_time
        logger.info(
            f"Brief generation complete in {elapsed_time:.2f}s: "
            f"{len(story_results)} successful, {len(failed_ids)} failed"
        )
        
        response = BriefResponse(
            stories=story_results,
            requested_n=request.n,
            returned_n=len(story_results),
            effective_topic=request.topic,
            time_range_label=request.time_range,
            summary_mode=request.summary_mode,
            partial_notice=partial_notice,
            error=None
        )
        
        return response
        
    except SearchError as e:
        logger.error(f"Search failed: {str(e)}")
        return BriefResponse(
            stories=[],
            requested_n=request.n,
            returned_n=0,
            effective_topic=request.topic,
            time_range_label=request.time_range,
            summary_mode=request.summary_mode,
            error=f"Failed to search for news: {str(e)}"
        )
    
    except Exception as e:
        logger.error(f"Unexpected error during brief generation: {type(e).__name__}: {str(e)}", exc_info=True)
        return BriefResponse(
            stories=[],
            requested_n=request.n,
            returned_n=0,
            effective_topic=request.topic,
            time_range_label=request.time_range,
            summary_mode=request.summary_mode,
            error=f"An unexpected error occurred: {str(e)}"
        )


def generate_multi_query_brief(entity_queries: dict, scoring_topic: str, n: int,
                               time_range: str, summary_mode: str = "Standard") -> BriefResponse:
    """
    Shared orchestration for multi-entity briefs (e.g., per-OEM or per-company news).

    Runs one search per entity, tags each result with its entity, then reuses the
    same dedupe/score/select/summarize pipeline as generate_brief().

    Args:
        entity_queries: mapping of entity_label -> search query
        scoring_topic: topic string used for relevance scoring (not the search query itself)
        n: number of stories to return
        time_range: time range for news
        summary_mode: "Quick" or "Standard"

    Returns:
        BriefResponse with stories tagged by entity_label
    """
    start_time = time.time()
    entities = list(entity_queries.keys())
    logger.info(f"Generating multi-query brief: entities={entities}, n={n}")

    if not entity_queries:
        return BriefResponse(
            stories=[], requested_n=n, returned_n=0, effective_topic=scoring_topic,
            time_range_label=time_range, summary_mode=summary_mode,
            error="No entities selected."
        )

    candidate_pool_per_entity = max((n * CANDIDATE_MULTIPLIER) // max(len(entity_queries), 1) + 3, 5)

    try:
        raw_results = search_news_multi(entity_queries, time_range, candidate_pool_per_entity)

        if not raw_results:
            return BriefResponse(
                stories=[], requested_n=n, returned_n=0, effective_topic=scoring_topic,
                time_range_label=time_range, summary_mode=summary_mode,
                error="No news found for the selected entities in this time range."
            )

        selected_candidates, partial_notice = process_search_results(
            raw_results=raw_results, n=n, topic=scoring_topic, time_range=time_range
        )

        if not selected_candidates:
            return BriefResponse(
                stories=[], requested_n=n, returned_n=0, effective_topic=scoring_topic,
                time_range_label=time_range, summary_mode=summary_mode,
                error="No suitable news found after filtering."
            )

        story_results, failed_ids = summarize_stories(candidates=selected_candidates, summary_mode=summary_mode)

        elapsed = time.time() - start_time
        logger.info(
            f"Multi-query brief generated in {elapsed:.2f}s: "
            f"{len(story_results)} successful, {len(failed_ids)} failed"
        )

        return BriefResponse(
            stories=story_results,
            requested_n=n,
            returned_n=len(story_results),
            effective_topic=scoring_topic,
            time_range_label=time_range,
            summary_mode=summary_mode,
            partial_notice=partial_notice,
            error=None
        )

    except SearchError as e:
        logger.error(f"Search failed: {str(e)}")
        return BriefResponse(
            stories=[], requested_n=n, returned_n=0, effective_topic=scoring_topic,
            time_range_label=time_range, summary_mode=summary_mode,
            error=f"Failed to search for news: {str(e)}"
        )

    except Exception as e:
        logger.error(f"Unexpected error during multi-query brief generation: {type(e).__name__}: {str(e)}", exc_info=True)
        return BriefResponse(
            stories=[], requested_n=n, returned_n=0, effective_topic=scoring_topic,
            time_range_label=time_range, summary_mode=summary_mode,
            error=f"An unexpected error occurred: {str(e)}"
        )
