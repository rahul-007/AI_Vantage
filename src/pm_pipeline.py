import logging
import time
from typing import List

from src.models import PmBriefResponse, PmUpdateResult, SearchError
from src.config import PM_RSS_FEEDS
from src.rss_client import fetch_latest_entries
from src.pm_summarizer import summarize_entry

logger = logging.getLogger(__name__)


def generate_pm_brief(feed_names: List[str], since_days: int) -> PmBriefResponse:
    """Fetch latest entries from selected PM voice feeds and summarize each."""
    start_time = time.time()
    logger.info(f"Generating PM brief: feeds={feed_names}, since_days={since_days}")

    if not feed_names:
        return PmBriefResponse(results=[], feed_names=feed_names, since_days=since_days, error="No feeds selected.")

    all_entries = []
    for name in feed_names:
        feed_url = PM_RSS_FEEDS.get(name)
        if not feed_url:
            logger.warning(f"Unknown feed name '{name}', skipping")
            continue
        try:
            entries = fetch_latest_entries(name, feed_url, since_days)
            all_entries.extend(entries)
        except SearchError as e:
            logger.warning(f"Skipping feed '{name}': {e}")
            continue

    if not all_entries:
        return PmBriefResponse(
            results=[], feed_names=feed_names, since_days=since_days,
            error="No new entries found for the selected voices in this time range."
        )

    # Most recent first
    all_entries.sort(key=lambda e: e.published or "", reverse=True)

    results = []
    for entry in all_entries:
        summary = summarize_entry(entry)
        results.append(PmUpdateResult(entry=entry, summary=summary))

    elapsed = time.time() - start_time
    logger.info(f"PM brief generated in {elapsed:.2f}s: {len(results)} entries")

    return PmBriefResponse(results=results, feed_names=feed_names, since_days=since_days)
