import logging
from typing import List
from urllib.parse import urlparse
from tavily import TavilyClient
import time

from src.models import RawSearchResult, SearchError
from src.config import TAVILY_API_KEY, SEARCH_TIMEOUT, SEARCH_MAX_RETRIES, TIME_RANGE_OPTIONS

logger = logging.getLogger(__name__)

_client = TavilyClient(api_key=TAVILY_API_KEY)


def _derive_publisher(url: str) -> str | None:
    """Tavily has no dedicated publisher field, so fall back to the URL's domain."""
    netloc = urlparse(url).netloc
    return netloc.removeprefix("www.") or None


def search_news(topic: str, time_range: str, max_results: int) -> List[RawSearchResult]:
    """
    Search for news using Tavily.
    
    Args:
        topic: News topic to search for
        time_range: Time range filter (e.g., "Last 24 hours")
        max_results: Maximum number of results to return
        
    Returns:
        List of RawSearchResult objects
        
    Raises:
        SearchError: If search fails or times out
    """
    logger.info(f"Starting news search: topic='{topic}', time_range='{time_range}', max_results={max_results}")
    
    # Map time_range to Tavily time_range parameter
    tavily_time_range = TIME_RANGE_OPTIONS.get(time_range, "week")
    
    results = []
    attempt = 0
    
    while attempt < SEARCH_MAX_RETRIES:
        try:
            attempt += 1
            logger.debug(f"Search attempt {attempt}/{SEARCH_MAX_RETRIES}")
            
            start_time = time.time()
            
            # Perform Tavily news search
            response = _client.search(
                query=topic,
                topic="news",
                time_range=tavily_time_range,
                max_results=max_results,
                search_depth="basic",
                timeout=SEARCH_TIMEOUT
            )
            search_results = response.get("results", [])
            
            elapsed = time.time() - start_time
            logger.info(f"Search completed in {elapsed:.2f}s, found {len(search_results)} results")
            
            # Convert to RawSearchResult
            for i, result in enumerate(search_results):
                try:
                    url = result.get("url", "")
                    raw_result = RawSearchResult(
                        title=result.get("title", ""),
                        url=url,
                        publisher=_derive_publisher(url),
                        snippet=result.get("content", None),
                        date=result.get("published_date", None)
                    )
                    results.append(raw_result)
                    logger.debug(f"Result {i+1}: '{raw_result.title[:60]}...'")
                except Exception as e:
                    logger.warning(f"Failed to parse result {i+1}: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(results)} results from search")
            return results
            
        except Exception as e:
            logger.error(f"Search attempt {attempt} failed: {type(e).__name__}: {str(e)}")
            if attempt < SEARCH_MAX_RETRIES:
                logger.info(f"Retrying in 2 seconds...")
                time.sleep(2)
            else:
                raise SearchError(f"Failed to search after {SEARCH_MAX_RETRIES} attempts: {str(e)}")
    
    raise SearchError(f"No results found for topic: {topic}")


def search_news_multi(entity_queries: dict, time_range: str, max_results_per_query: int) -> List[RawSearchResult]:
    """
    Run one search per entity (e.g. OEM or company), tagging each result with its entity label.

    Args:
        entity_queries: mapping of entity_label -> query string
        time_range: Time range filter (e.g., "Last 24 hours")
        max_results_per_query: Maximum number of results to fetch per entity

    Returns:
        Combined list of RawSearchResult objects across all entities (failures are skipped, not raised)
    """
    combined: List[RawSearchResult] = []
    for entity_label, query in entity_queries.items():
        try:
            results = search_news(query, time_range, max_results_per_query)
            for result in results:
                result.entity_label = entity_label
            combined.extend(results)
        except SearchError as e:
            logger.warning(f"Search failed for entity '{entity_label}' (query='{query}'): {e}")
            continue
    return combined
