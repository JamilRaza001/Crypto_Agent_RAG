"""
Source display component - shows source citations and confidence indicators.
"""

import streamlit as st


def render_sources(sources: list, confidence: float = None):
    """
    Render source citations panel.

    Args:
        sources: List of source dictionaries
        confidence: Overall confidence score
    """

    if not sources:
        st.info("No sources yet. Ask a question to see sources used!")
        return

    # Display confidence indicator
    if confidence:
        st.markdown("#### Confidence Score")
        if confidence >= 0.8:
            st.success(f"🟢 High Confidence: {confidence:.2%}")
        elif confidence >= 0.6:
            st.warning(f"🟡 Medium Confidence: {confidence:.2%}")
        else:
            st.error(f"🔴 Low Confidence: {confidence:.2%}")

        st.markdown("---")

    # Group sources by type
    kb_sources = [s for s in sources if s.get('type') == 'knowledge_base']
    api_sources = [s for s in sources if s.get('type') == 'api']

    # Knowledge Base sources
    if kb_sources:
        st.markdown("#### 📚 Knowledge Base")

        for i, source in enumerate(kb_sources, 1):
            with st.expander(f"Source {i}: {source.get('title', 'Unknown')}", expanded=False):
                st.markdown(f"**Category:** {source.get('category', 'Unknown')}")

                similarity = source.get('similarity', 0)
                st.markdown(f"**Similarity:** {similarity:.2%}")

                # Similarity indicator
                if similarity >= 0.8:
                    st.markdown("🟢 Highly relevant")
                elif similarity >= 0.7:
                    st.markdown("🟡 Relevant")
                else:
                    st.markdown("🟠 Moderately relevant")

                st.markdown(f"**Preview:**")
                st.text(source.get('content_preview', 'N/A'))

    # API sources
    if api_sources:
        if kb_sources:
            st.markdown("---")

        st.markdown("#### 🌐 Live API Data")

        for i, source in enumerate(api_sources, 1):
            with st.expander(f"API {i}: {source.get('endpoint', 'Unknown')}", expanded=False):
                st.markdown(f"**Endpoint:** `{source.get('endpoint', 'Unknown')}`")
                st.markdown(f"**Timestamp:** {source.get('timestamp', 'N/A')}")
                st.markdown(f"**Data Preview:**")
                st.code(source.get('data_preview', 'N/A'), language="json")

    # Stats
    st.markdown("---")
    st.markdown(f"**Total Sources:** {len(sources)} ({len(kb_sources)} KB, {len(api_sources)} API)")
