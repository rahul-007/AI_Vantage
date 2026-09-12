import logging
from typing import List

from src.models import BriefResponse
from src.config import IAM_SECURITY_QUERY_TEMPLATE, IAM_SECURITY_SCORING_TOPIC
from src.pipeline import generate_multi_query_brief

logger = logging.getLogger(__name__)


def generate_iam_brief(companies: List[str], n: int, time_range: str, summary_mode: str = "Standard") -> BriefResponse:
    """Generate an IAM/cybersecurity news brief across the selected companies."""
    entity_queries = {company: IAM_SECURITY_QUERY_TEMPLATE.format(company=company) for company in companies}
    return generate_multi_query_brief(
        entity_queries=entity_queries,
        scoring_topic=IAM_SECURITY_SCORING_TOPIC,
        n=n,
        time_range=time_range,
        summary_mode=summary_mode,
    )
