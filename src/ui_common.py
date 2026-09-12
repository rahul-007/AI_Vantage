import streamlit as st
from datetime import datetime, timezone


def render_page_header(icon: str, title: str, description: str):
    """Render a consistent page title + description block."""
    st.title(f"{icon} {title}")
    st.markdown(description, unsafe_allow_html=False)


def render_story_card(idx: int, headline: str, body: str, meta_parts: list, url: str = None, caption: str = None):
    """Render a single story/result card with a consistent layout across pages."""
    with st.container(border=True):
        st.markdown(f"### {idx}. {headline}", unsafe_allow_html=False)
        st.markdown(body, unsafe_allow_html=False)

        if meta_parts:
            st.markdown(" | ".join(meta_parts), unsafe_allow_html=False)

        if caption:
            st.caption(caption)

        if url:
            st.markdown(f"[📖 Read Original Article]({url})", unsafe_allow_html=False)


def render_error(error: str) -> bool:
    """Render an error banner if present. Returns True if an error was shown."""
    if error:
        st.error(f"❌ {error}")
        return True
    return False


def render_partial_notice(notice: str):
    """Render an info banner for partial-result notices."""
    if notice:
        st.info(f"ℹ️ {notice}")


def render_footer(note: str = "Always verify summaries against original sources."):
    """Render a consistent footer with a generation timestamp."""
    st.divider()
    st.caption(
        f"Generated at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC. {note}"
    )
