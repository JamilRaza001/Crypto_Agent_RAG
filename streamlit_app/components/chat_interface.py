"""
Chat interface component for Streamlit.
"""

import streamlit as st
from src.utils.logging_config import logger


def render_chat_interface():
    """Render the chat interface."""

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            # Show confidence indicator if available
            if message["role"] == "assistant" and "confidence" in message:
                confidence = message["confidence"]
                if confidence:
                    if confidence >= 0.8:
                        indicator = "🟢 High confidence"
                        color = "green"
                    elif confidence >= 0.6:
                        indicator = "🟡 Medium confidence"
                        color = "orange"
                    else:
                        indicator = "🔴 Low confidence"
                        color = "red"

                    st.markdown(
                        f'<small style="color: {color};">{indicator} ({confidence:.2f})</small>',
                        unsafe_allow_html=True
                    )

    # Chat input
    if prompt := st.chat_input("Ask about cryptocurrency or blockchain..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Process query
                    response = st.session_state.agent.process_query(prompt, stream=False)

                    # Display response
                    st.markdown(response['text'])

                    # Update session state with sources and confidence
                    st.session_state.last_sources = response.get('sources', [])
                    st.session_state.last_confidence = response.get('confidence')

                    # Show confidence
                    if response.get('confidence'):
                        confidence = response['confidence']
                        if confidence >= 0.8:
                            indicator = "🟢 High confidence"
                            color = "green"
                        elif confidence >= 0.6:
                            indicator = "🟡 Medium confidence"
                            color = "orange"
                        else:
                            indicator = "🔴 Low confidence"
                            color = "red"

                        st.markdown(
                            f'<small style="color: {color};">{indicator} ({confidence:.2f})</small>',
                            unsafe_allow_html=True
                        )

                    # Add assistant message
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response['text'],
                        "confidence": response.get('confidence')
                    })

                    # Force rerun to update sources panel
                    st.rerun()

                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    logger.exception("Error processing query in Streamlit")

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })
