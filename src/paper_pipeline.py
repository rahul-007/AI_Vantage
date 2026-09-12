import logging
import time
from typing import List

from src.models import PaperBriefResponse, PaperBriefResult, SearchError
from src.arxiv_client import fetch_recent_papers
from src.paper_explainer import explain_paper

logger = logging.getLogger(__name__)


def generate_paper_brief(categories: List[str], n: int) -> PaperBriefResponse:
    """Fetch recent arXiv papers and explain each in plain language."""
    start_time = time.time()
    logger.info(f"Generating paper brief: categories={categories}, n={n}")

    try:
        papers = fetch_recent_papers(categories, n)
    except SearchError as e:
        logger.error(f"Paper fetch failed: {str(e)}")
        return PaperBriefResponse(results=[], requested_n=n, returned_n=0, categories=categories, error=str(e))

    if not papers:
        return PaperBriefResponse(
            results=[], requested_n=n, returned_n=0, categories=categories,
            error="No papers found for the selected categories."
        )

    results = []
    failed = 0
    for paper in papers:
        explanation = explain_paper(paper)
        if explanation:
            results.append(PaperBriefResult(paper=paper, explanation=explanation))
        else:
            failed += 1

    partial_notice = None
    if failed:
        partial_notice = f"{failed} paper(s) could not be explained and were skipped."

    elapsed = time.time() - start_time
    logger.info(f"Paper brief generated in {elapsed:.2f}s: {len(results)} successful, {failed} failed")

    return PaperBriefResponse(
        results=results,
        requested_n=n,
        returned_n=len(results),
        categories=categories,
        partial_notice=partial_notice,
    )
