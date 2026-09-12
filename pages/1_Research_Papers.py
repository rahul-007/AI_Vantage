import streamlit as st
import logging

from src.logging_config import setup_logging
from src.paper_pipeline import generate_paper_brief
from src.ui_common import render_page_header, render_error, render_partial_notice, render_footer
from src.config import ARXIV_CATEGORY_OPTIONS, ARXIV_DEFAULT_CATEGORIES, ARXIV_N_OPTIONS

setup_logging()
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Research Papers", page_icon="🔬", layout="wide")


def render_paper_card(idx: int, result):
    """Render a single paper card with metadata, links, and its plain-language explanation."""
    paper = result.paper
    explanation = result.explanation

    with st.container(border=True):
        st.markdown(f"### {idx}. {paper.title}", unsafe_allow_html=False)

        authors_str = ", ".join(paper.authors[:5]) + (" et al." if len(paper.authors) > 5 else "")
        st.markdown(f"*{authors_str}* | {paper.published} | `{paper.primary_category}`")
        st.markdown(f"[📄 Abstract]({paper.entry_url}) | [📥 PDF]({paper.pdf_url})")

        if explanation:
            with st.expander("💡 Explain in plain language", expanded=True):
                st.markdown(f"**Problem:** {explanation.problem}")
                st.markdown(f"**Approach:** {explanation.approach}")
                st.markdown(f"**Key Results:** {explanation.key_results}")
                st.markdown(f"**Why It Matters:** {explanation.why_it_matters}")
                st.markdown(f"**Limitations:** {explanation.limitations}")
        else:
            st.caption("⚠️ Plain-language explanation unavailable for this paper.")


def main():
    render_page_header(
        "🔬", "Research Papers",
        "Latest AI/ML research papers from arXiv, explained in plain language."
    )

    st.subheader("📋 Quick Start")
    category_labels = st.multiselect(
        "Categories:",
        options=list(ARXIV_CATEGORY_OPTIONS.keys()),
        default=[label for label, code in ARXIV_CATEGORY_OPTIONS.items() if code in ARXIV_DEFAULT_CATEGORIES],
    )
    n = st.radio("How many papers?", options=ARXIV_N_OPTIONS, horizontal=True)
    generate = st.button("🚀 Generate Papers Brief", use_container_width=True, type="primary")

    if generate:
        if not category_labels:
            st.error("Please select at least one category.")
            return

        categories = list(dict.fromkeys(ARXIV_CATEGORY_OPTIONS[label] for label in category_labels))

        with st.status("Fetching and explaining papers...", expanded=True) as status:
            status.update(label="📚 Fetching recent papers from arXiv...", state="running")
            try:
                response = generate_paper_brief(categories, n)
                status.update(label="✅ Papers ready!", state="complete")
            except Exception as e:
                logger.error(f"Error generating paper brief: {type(e).__name__}: {str(e)}")
                status.update(label="❌ Error", state="error")
                st.error(f"An error occurred: {str(e)}")
                return

        st.divider()
        if render_error(response.error):
            return
        render_partial_notice(response.partial_notice)

        if not response.results:
            st.warning("No papers found. Try different categories.")
            return

        st.subheader(f"🔬 Research Papers ({response.returned_n})")
        for idx, result in enumerate(response.results, 1):
            render_paper_card(idx, result)

        render_footer("Explanations are generated from abstracts only; always check the full paper for details.")


if __name__ == "__main__":
    main()
