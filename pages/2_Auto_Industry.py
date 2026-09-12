import streamlit as st
import logging

from src.logging_config import setup_logging
from src.auto_pipeline import generate_auto_brief
from src.ui_common import render_page_header, render_story_card, render_error, render_partial_notice, render_footer
from src.config import AUTO_OEM_GROUPS, N_OPTIONS, TIME_RANGE_OPTIONS, SUMMARY_MODES

setup_logging()
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Auto Industry", page_icon="🚗", layout="wide")


def main():
    render_page_header(
        "🚗", "Auto Industry Connected Services",
        "Track the latest connected-car, infotainment, and software-defined vehicle features "
        "from Chinese OEMs and Western/Stellantis competitors."
    )

    st.subheader("📋 Quick Start")

    selected_oems = []
    for group_name, oems in AUTO_OEM_GROUPS.items():
        st.markdown(f"**{group_name}**")
        default_checked = group_name == "Chinese OEMs"
        cols = st.columns(3)
        for i, oem in enumerate(oems):
            with cols[i % 3]:
                if st.checkbox(oem, value=default_checked, key=f"oem_{oem}"):
                    selected_oems.append(oem)

    st.sidebar.header("⚙️ Advanced Options")
    n = st.sidebar.radio("How many stories?", options=N_OPTIONS)
    time_range = st.sidebar.radio("News from:", options=list(TIME_RANGE_OPTIONS.keys()))
    summary_mode = st.sidebar.radio("Summary length:", options=SUMMARY_MODES)

    generate = st.button("🚀 Generate Auto Industry Brief", use_container_width=True, type="primary")

    if generate:
        if not selected_oems:
            st.error("Please select at least one OEM.")
            return

        with st.status("Generating your briefing...", expanded=True) as status:
            status.update(label="🔍 Searching for OEM news...", state="running")
            try:
                response = generate_auto_brief(selected_oems, n, time_range, summary_mode)
                status.update(label="✅ Brief ready!", state="complete")
            except Exception as e:
                logger.error(f"Error generating auto brief: {type(e).__name__}: {str(e)}")
                status.update(label="❌ Error", state="error")
                st.error(f"An error occurred: {str(e)}")
                return

        st.divider()
        if render_error(response.error):
            return
        render_partial_notice(response.partial_notice)

        if not response.stories:
            st.warning("No stories found. Try different OEMs or a wider time range.")
            return

        st.subheader(f"🚗 Connected Services News ({response.returned_n} stories)")
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
