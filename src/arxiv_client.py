import logging
from typing import List
import arxiv

from src.models import ArxivPaper, SearchError

logger = logging.getLogger(__name__)


def fetch_recent_papers(categories: List[str], max_results: int) -> List[ArxivPaper]:
    """Fetch the most recently submitted arXiv papers across the given categories."""
    if not categories:
        raise SearchError("At least one arXiv category must be selected.")

    category_query = " OR ".join(f"cat:{c}" for c in categories)
    logger.info(f"Fetching arXiv papers: query='{category_query}', max_results={max_results}")

    try:
        search = arxiv.Search(
            query=category_query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending,
        )
        client = arxiv.Client()

        papers = []
        for result in client.results(search):
            papers.append(ArxivPaper(
                paper_id=result.get_short_id(),
                title=result.title.strip().replace("\n", " "),
                authors=[a.name for a in result.authors],
                abstract=result.summary.strip().replace("\n", " "),
                pdf_url=result.pdf_url,
                entry_url=result.entry_id,
                published=result.published.strftime("%Y-%m-%d"),
                primary_category=result.primary_category,
            ))

        logger.info(f"Fetched {len(papers)} arXiv papers")
        return papers

    except SearchError:
        raise
    except Exception as e:
        logger.error(f"arXiv fetch failed: {type(e).__name__}: {str(e)}")
        raise SearchError(f"Failed to fetch arXiv papers: {str(e)}")
