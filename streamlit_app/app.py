"""
Main Streamlit application for the Crypto Agent.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from src.agent.crypto_agent import get_crypto_agent
from streamlit_app.components.chat_interface import render_chat_interface
from streamlit_app.components.source_display import render_sources
from streamlit_app.components.sidebar import render_sidebar


# Page configuration
st.set_page_config(
    page_title="Crypto Knowledge Agent",
    page_icon="🪙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


def initialize_knowledge_base():
    """Initialize knowledge base on first deployment if needed."""
    import os
    from config.settings import settings

    # Check if ChromaDB exists
    chroma_path = Path(settings.chroma_db_path)
    chroma_sqlite = chroma_path / "chroma.sqlite3"

    if not chroma_sqlite.exists():
        st.info("🔄 First-time setup: Initializing knowledge base...")
        st.info("This may take 2-3 minutes. Please wait...")

        try:
            # Import and run initialization
            from scripts.init_kb import main as init_kb_main
            init_kb_main()
            st.success("✅ Knowledge base initialized successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error initializing knowledge base: {e}")
            st.stop()


def initialize_session_state():
    """Initialize Streamlit session state."""
    if 'agent' not in st.session_state:
        st.session_state.agent = get_crypto_agent()

    if 'messages' not in st.session_state:
        st.session_state.messages = []

    if 'last_sources' not in st.session_state:
        st.session_state.last_sources = []

    if 'last_confidence' not in st.session_state:
        st.session_state.last_confidence = None


def main():
    """Main application."""
    # Initialize KB on first run (for cloud deployment)
    initialize_knowledge_base()

    initialize_session_state()

    # Header
    st.markdown('<div class="main-header">🪙 Crypto Knowledge Agent</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Knowledge-grounded cryptocurrency assistant with zero hallucinations</div>',
        unsafe_allow_html=True
    )

    # Sidebar
    render_sidebar()

    # Main chat interface
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 💬 Chat")
        render_chat_interface()

    with col2:
        st.markdown("### 📚 Sources")
        render_sources(
            st.session_state.last_sources,
            st.session_state.last_confidence
        )


if __name__ == "__main__":
    main()
