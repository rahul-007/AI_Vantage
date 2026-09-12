import logging
from typing import List

from src.models import BriefResponse
from src.config import AI_RELEASES_QUERY_TEMPLATE, AI_RELEASES_SCORING_TOPIC
from src.pipeline import generate_multi_query_brief

logger = logging.getLogger(__name__)


def generate_releases_brief(companies: List[str], n: int, time_range: str, summary_mode: str = "Standard") -> BriefResponse:
    """Generate a product-launch news brief across the selected AI companies."""
    entity_queries = {company: AI_RELEASES_QUERY_TEMPLATE.format(company=company) for company in companies}
    return generate_multi_query_brief(
        entity_queries=entity_queries,
        scoring_topic=AI_RELEASES_SCORING_TOPIC,
        n=n,
        time_range=time_range,
        summary_mode=summary_mode,
    )
