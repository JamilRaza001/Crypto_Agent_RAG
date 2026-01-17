"""
Sidebar component with agent stats and controls.
"""

import streamlit as st


def render_sidebar():
    """Render the sidebar with stats and controls."""

    with st.sidebar:
        st.markdown("## ⚙️ Settings")

        # Clear conversation button
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            st.session_state.agent.clear_conversation()
            st.session_state.messages = []
            st.session_state.last_sources = []
            st.session_state.last_confidence = None
            st.success("Conversation cleared!")
            st.rerun()

        st.markdown("---")

        # Agent stats
        st.markdown("## 📊 Agent Statistics")

        try:
            stats = st.session_state.agent.get_stats()

            # Conversation stats
            st.markdown("### 💬 Conversation")
            conv_stats = stats.get('conversation', {})
            st.metric("Turns", conv_stats.get('num_turns', 0))

            entities = conv_stats.get('entities', [])
            if entities:
                st.markdown("**Tracked Entities:**")
                st.write(", ".join(entities[:5]))

            st.markdown("---")

            # Rate limit stats
            st.markdown("### 🚦 API Rate Limit")
            rate_stats = stats.get('rate_limit', {})

            if rate_stats:
                used = rate_stats.get('request_count', 0)
                total = rate_stats.get('monthly_limit', 100000)
                remaining = rate_stats.get('remaining', total)
                percentage = rate_stats.get('percentage_used', 0)

                st.metric("Requests Used", f"{used:,} / {total:,}")
                st.progress(percentage / 100)

                if percentage >= 80:
                    st.warning(f"⚠️ {percentage}% of monthly limit used")
                else:
                    st.info(f"{remaining:,} requests remaining")

                st.caption(f"Resets: {rate_stats.get('reset_date', 'Unknown')}")

            st.markdown("---")

            # Cache stats
            st.markdown("### 💾 Cache")
            cache_stats = stats.get('cache', {})

            if cache_stats:
                st.metric("Active Entries", cache_stats.get('active_entries', 0))
                st.metric("Total Hits", cache_stats.get('total_hits', 0))

                top_endpoints = cache_stats.get('top_endpoints', [])
                if top_endpoints:
                    st.markdown("**Most Cached:**")
                    for endpoint_data in top_endpoints[:3]:
                        if isinstance(endpoint_data, dict):
                            endpoint = endpoint_data.get('endpoint', 'Unknown')
                            hits = endpoint_data.get('hits', 0)
                            st.caption(f"• {endpoint}: {hits} hits")

        except Exception as e:
            st.error(f"Error loading stats: {e}")

        st.markdown("---")

        # About
        st.markdown("## ℹ️ About")
        st.markdown("""
        **Knowledge-Grounded Crypto Agent**

        Features:
        - ✅ Zero hallucinations
        - 📚 45+ crypto knowledge docs
        - 🌐 Real-time market data
        - 🔒 Multi-layer validation
        - 💬 Entity tracking

        Built with:
        - Streamlit
        - Google Gemini
        - ChromaDB
        - FreeCryptoAPI
        """)

        st.markdown("---")
        st.caption("v1.0.0 | Built with Claude Code")
