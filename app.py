import streamlit as st
import logging

from src.logging_config import setup_logging
from src.models import BriefRequest
from src.pipeline import generate_brief
from src.ui_common import render_page_header, render_story_card, render_error, render_partial_notice, render_footer
from src.config import (
    TOPIC_PRESETS, N_OPTIONS, TIME_RANGE_OPTIONS, 
    SUMMARY_MODES, CUSTOM_TOPIC_MAX_LENGTH
)

# Initialize logging once at startup
setup_logging()
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="AI News Briefing",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

logger.info("Streamlit app started")


def render_header():
    """Render page header."""
    render_page_header(
        "📰", "AI News Briefing",
        "Stay informed with AI-powered news summaries. Select a topic, configure your preferences, "
        "and get a curated briefing of the most relevant recent news."
    )


def render_quick_start():
    """Render topic input and Generate button in the main area (visible without opening the sidebar)."""
    st.subheader("📋 Quick Start")
    
    topic_choice = st.radio(
        "Select a topic:",
        options=["Predefined"] + ["Custom"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    if topic_choice == "Predefined":
        topic = st.selectbox(
            "Choose a topic:",
            options=TOPIC_PRESETS,
            label_visibility="collapsed"
        )
    else:
        topic = st.text_input(
            "Enter custom topic:",
            max_chars=CUSTOM_TOPIC_MAX_LENGTH,
            placeholder="e.g., AI regulation in Europe",
            label_visibility="collapsed"
        )
    
    st.caption("Tune story count, timeframe, and summary length in the sidebar (tap ☰ if hidden).")
    
    generate_button = st.button(
        "🚀 Generate Brief",
        use_container_width=True,
        type="primary"
    )
    
    return {
        "topic": topic,
        "generate": generate_button
    }


def render_advanced_options():
    """Render fine-tuning options in the sidebar, with sensible defaults preselected."""
    st.sidebar.header("⚙️ Advanced Options")
    
    # Number of stories
    st.sidebar.subheader("Number of Stories")
    n = st.sidebar.radio(
        "How many stories?",
        options=N_OPTIONS,
        label_visibility="collapsed"
    )
    
    # Time range
    st.sidebar.subheader("Time Range")
    time_range = st.sidebar.radio(
        "News from:",
        options=list(TIME_RANGE_OPTIONS.keys()),
        label_visibility="collapsed"
    )
    
    # Summary length
    st.sidebar.subheader("Summary Length")
    summary_mode = st.sidebar.radio(
        "Preferred length:",
        options=SUMMARY_MODES,
        label_visibility="collapsed"
    )
    
    return {
        "n": n,
        "time_range": time_range,
        "summary_mode": summary_mode
    }


def render_results(response):
    """Render briefing results."""
    # Header with parameters
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Topic", response.effective_topic)
    with col2:
        st.metric("Time Range", response.time_range_label)
    with col3:
        st.metric("Stories Requested", response.requested_n)
    with col4:
        st.metric("Stories Returned", response.returned_n)
    
    st.divider()
    
    # Error state
    if render_error(response.error):
        return
    
    # Partial notice
    render_partial_notice(response.partial_notice)
    
    # No stories
    if not response.stories:
        st.warning("No stories found. Please try different search parameters.")
        return
    
    # Render stories
    st.subheader(f"📰 News Briefing ({response.returned_n} stories)")
    
    for idx, story in enumerate(response.stories, 1):
        source_parts = []
        if story.publisher:
            source_parts.append(f"**{story.publisher}**")
        if story.published_at:
            source_parts.append(f"*{story.published_at}*")
        
        render_story_card(
            idx=idx,
            headline=story.headline,
            body=story.summary,
            meta_parts=source_parts,
            url=story.source_url,
            caption=f"⚠️ {story.content_limitations}" if story.content_limitations else None
        )


def main():
    """Main application flow."""
    render_header()
    
    # Render quick-start (main area) and advanced options (sidebar), then merge
    quick_start_values = render_quick_start()
    advanced_values = render_advanced_options()
    form_values = {**quick_start_values, **advanced_values}
    
    # Validate and process input
    if form_values["generate"]:
        # Validate topic
        if not form_values["topic"] or not form_values["topic"].strip():
            st.error("Please enter or select a topic.")
            return
        
        logger.info(f"Generating brief with: {form_values}")
        
        # Show progress
        with st.status("Generating your briefing...", expanded=True) as status:
            status.update(label="🔍 Searching for current news...", state="running")
            logger.debug("Starting news search...")
            
            status.update(label="🔍 Searching... | 📋 Reviewing relevant sources...", state="running")
            logger.debug("Processing results...")
            
            status.update(label="🔍 Searching... | 📋 Reviewing... | 🧹 Removing duplicates...", state="running")
            logger.debug("Deduplicating results...")
            
            status.update(label="🔍 Searching... | 📋 Reviewing... | 🧹 Removing... | 📝 Preparing summary...", state="running")
            logger.debug("Summarizing stories...")
            
            # Create brief request
            request = BriefRequest(
                topic=form_values["topic"].strip(),
                n=form_values["n"],
                time_range=form_values["time_range"],
                summary_mode=form_values["summary_mode"]
            )
            
            try:
                # Generate brief
                response = generate_brief(request)
                logger.info(f"Brief generated: {response.returned_n} stories returned")
                
                status.update(label="✅ Brief ready!", state="complete")
            
            except Exception as e:
                logger.error(f"Error during brief generation: {type(e).__name__}: {str(e)}")
                status.update(label="❌ Error generating brief", state="error")
                st.error(f"An error occurred: {str(e)}")
                return
        
        # Render results
        st.divider()
        render_results(response)
        
        # Footer
        render_footer()


if __name__ == "__main__":
    logger.info("Main execution started")
    main()
