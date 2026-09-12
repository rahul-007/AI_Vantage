import streamlit as st
import logging

from src.logging_config import setup_logging
from src.iam_pipeline import generate_iam_brief
from src.ui_common import render_page_header, render_story_card, render_error, render_partial_notice, render_footer
from src.config import IAM_SECURITY_COMPANIES, N_OPTIONS, TIME_RANGE_OPTIONS, SUMMARY_MODES

setup_logging()
logger = logging.getLogger(__name__)

st.set_page_config(page_title="IAM & Cybersecurity", page_icon="🔐", layout="wide")


def main():
    render_page_header(
        "🔐", "Identity & Access Management / Cybersecurity",
        "Track the latest identity, authentication, and cybersecurity developments "
        "from leading IAM and security vendors."
    )

    st.subheader("📋 Quick Start")

    selected_companies = []
    cols = st.columns(3)
    for i, company in enumerate(IAM_SECURITY_COMPANIES):
        with cols[i % 3]:
            if st.checkbox(company, value=True, key=f"iam_{company}"):
                selected_companies.append(company)

    st.sidebar.header("⚙️ Advanced Options")
    n = st.sidebar.radio("How many stories?", options=N_OPTIONS)
    time_range = st.sidebar.radio("News from:", options=list(TIME_RANGE_OPTIONS.keys()))
    summary_mode = st.sidebar.radio("Summary length:", options=SUMMARY_MODES)

    generate = st.button("🚀 Generate IAM & Cybersecurity Brief", use_container_width=True, type="primary")

    if generate:
        if not selected_companies:
            st.error("Please select at least one company.")
            return

        with st.status("Generating your briefing...", expanded=True) as status:
            status.update(label="🔍 Searching for IAM & cybersecurity news...", state="running")
            try:
                response = generate_iam_brief(selected_companies, n, time_range, summary_mode)
                status.update(label="✅ Brief ready!", state="complete")
            except Exception as e:
                logger.error(f"Error generating IAM brief: {type(e).__name__}: {str(e)}")
                status.update(label="❌ Error", state="error")
                st.error(f"An error occurred: {str(e)}")
                return

        st.divider()
        if render_error(response.error):
            return
        render_partial_notice(response.partial_notice)

        if not response.stories:
            st.warning("No stories found. Try different companies or a wider time range.")
            return

        st.subheader(f"🔐 IAM & Cybersecurity News ({response.returned_n} stories)")
        for idx, story in enumerate(response.stories, 1):
            meta_parts = []
            if story.entity_label:
                meta_parts.append(f"🏷️ **{story.entity_label}**")
            if story.publisher:
                meta_parts.append(f"**{story.publisher}**")
            if story.published_at:
                meta_parts.append(f"*{story.published_at}*")

            render_story_card(
                idx=idx,
                headline=story.headline,
                body=story.summary,
                meta_parts=meta_parts,
                url=story.source_url,
                caption=f"⚠️ {story.content_limitations}" if story.content_limitations else None
            )

        render_footer()


if __name__ == "__main__":
    main()
