import streamlit as st
import logging

from src.logging_config import setup_logging
from src.pm_pipeline import generate_pm_brief
from src.ui_common import render_page_header, render_error, render_footer
from src.config import PM_RSS_FEEDS, PM_SINCE_DAYS_OPTIONS, PM_DEFAULT_SINCE_DAYS

setup_logging()
logger = logging.getLogger(__name__)

st.set_page_config(page_title="PM Updates", page_icon="🧠", layout="wide")


def render_pm_card(idx: int, result):
    """Render a single PM update card: creator, title, date, link, and grounded summary."""
    entry = result.entry

    with st.container(border=True):
        st.markdown(f"### {idx}. {entry.title}", unsafe_allow_html=False)

        meta_parts = [f"**{entry.source_name}**"]
        if entry.published:
            meta_parts.append(f"*{entry.published}*")
        st.markdown(" | ".join(meta_parts), unsafe_allow_html=False)

        if result.summary:
            st.markdown(result.summary, unsafe_allow_html=False)
        else:
            st.caption("⚠️ Summary unavailable for this entry.")

        if entry.link:
            st.markdown(f"[📖 Read/Listen]({entry.link})", unsafe_allow_html=False)


def main():
    render_page_header(
        "🧠", "PM Voices Updates",
        "Stay on top of the latest posts and podcast episodes from popular product voices."
    )

    st.subheader("📋 Quick Start")
    feed_names = list(PM_RSS_FEEDS.keys())
    selected_feeds = []
    for feed_name in feed_names:
        if st.checkbox(feed_name, value=True, key=f"feed_{feed_name}"):
            selected_feeds.append(feed_name)

    since_days = st.radio(
        "Show updates from the last:",
        options=PM_SINCE_DAYS_OPTIONS,
        index=PM_SINCE_DAYS_OPTIONS.index(PM_DEFAULT_SINCE_DAYS),
        format_func=lambda d: f"{d} days",
        horizontal=True
    )

    generate = st.button("🚀 Generate PM Updates", use_container_width=True, type="primary")

    if generate:
        if not selected_feeds:
            st.error("Please select at least one voice/feed.")
            return

        with st.status("Fetching and summarizing updates...", expanded=True) as status:
            status.update(label="🔍 Fetching latest posts/episodes...", state="running")
            try:
                response = generate_pm_brief(selected_feeds, since_days)
                status.update(label="✅ Updates ready!", state="complete")
            except Exception as e:
                logger.error(f"Error generating PM brief: {type(e).__name__}: {str(e)}")
                status.update(label="❌ Error", state="error")
                st.error(f"An error occurred: {str(e)}")
                return

        st.divider()
        if render_error(response.error):
            return

        if not response.results:
            st.warning("No updates found. Try a wider time range.")
            return

        st.subheader(f"🧠 PM Voices Updates ({len(response.results)})")
        for idx, result in enumerate(response.results, 1):
            render_pm_card(idx, result)

        render_footer("Summaries are grounded in the feed's title/description only.")


if __name__ == "__main__":
    main()
