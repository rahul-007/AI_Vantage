import logging
from typing import List

from src.models import BriefResponse
from src.config import AUTO_QUERY_TEMPLATE, AUTO_SCORING_TOPIC
from src.pipeline import generate_multi_query_brief

logger = logging.getLogger(__name__)


def generate_auto_brief(oems: List[str], n: int, time_range: str, summary_mode: str = "Standard") -> BriefResponse:
    """Generate a connected-services news brief across the selected OEMs."""
    entity_queries = {oem: AUTO_QUERY_TEMPLATE.format(oem=oem) for oem in oems}
    return generate_multi_query_brief(
        entity_queries=entity_queries,
        scoring_topic=AUTO_SCORING_TOPIC,
        n=n,
        time_range=time_range,
        summary_mode=summary_mode,
    )
