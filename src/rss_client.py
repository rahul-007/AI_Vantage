import logging
import re
from datetime import datetime, timedelta, timezone
from typing import List
import feedparser

from src.models import RssEntry, SearchError

logger = logging.getLogger(__name__)

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    """Remove HTML tags from a feed description, leaving plain text."""
    if not text:
        return ""
    return _TAG_RE.sub("", text).strip()


def fetch_latest_entries(source_name: str, feed_url: str, since_days: int) -> List[RssEntry]:
    """
    Fetch entries from an RSS/Atom feed published within the last `since_days` days.

    Args:
        source_name: display name for the feed (e.g. "Lenny's Newsletter")
        feed_url: the RSS/Atom feed URL
        since_days: only return entries published within this many days

    Returns:
        List of RssEntry objects, most recent first

    Raises:
        SearchError: if the feed cannot be fetched or parsed
    """
    logger.info(f"Fetching RSS feed: source='{source_name}', url='{feed_url}', since_days={since_days}")

    try:
        parsed = feedparser.parse(feed_url)
    except Exception as e:
        logger.error(f"Failed to parse feed '{feed_url}': {type(e).__name__}: {str(e)}")
        raise SearchError(f"Failed to fetch feed for {source_name}: {str(e)}")

    if parsed.bozo and not parsed.entries:
        raise SearchError(f"Failed to parse feed for {source_name}: {parsed.bozo_exception}")

    cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
    entries = []

    for item in parsed.entries:
        published_struct = item.get("published_parsed") or item.get("updated_parsed")
        published_str = None
        if published_struct:
            published_dt = datetime(*published_struct[:6], tzinfo=timezone.utc)
            published_str = published_dt.strftime("%Y-%m-%d")
            if published_dt < cutoff:
                continue

        entries.append(RssEntry(
            source_name=source_name,
            title=item.get("title", "Untitled"),
            link=item.get("link", ""),
            published=published_str,
            description=_strip_html(item.get("summary", ""))[:1000]
        ))

    logger.info(f"Found {len(entries)} entries for '{source_name}' within the last {since_days} days")
    return entries
