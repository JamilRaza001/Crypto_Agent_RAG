"""
Main Crypto Agent - orchestrates all components for end-to-end query handling.
This is the primary interface for the Streamlit app.
"""

from typing import Dict, Optional, Generator
from src.agent.query_processor import get_query_processor
from src.agent.tool_orchestrator import get_tool_orchestrator
from src.agent.response_generator import get_response_generator
from src.agent.conversation_manager import get_conversation_manager
from src.utils.logging_config import logger


class CryptoAgent:
    """Main crypto agent orchestrating all components."""

    def __init__(self):
        """Initialize crypto agent."""
        self.query_processor = get_query_processor()
        self.tool_orchestrator = get_tool_orchestrator()
        self.response_generator = get_response_generator()
        self.conversation_manager = get_conversation_manager()

        logger.info("Crypto Agent initialized")

    def process_query(self, query: str, stream: bool = False) -> Dict:
        """
        Process user query end-to-end.

        Args:
            query: User query
            stream: Whether to stream response

        Returns:
            Response dictionary with text, sources, and metadata
        """
        logger.info(f"=== Processing Query: '{query}' ===")

        # Step 1: Process query
        query_analysis = self.query_processor.process(
            query,
            conversation_context=self.conversation_manager.get_context_for_llm()
        )

        logger.info(f"Query analysis: {query_analysis}")

        # Step 2: Orchestrate tool execution
        kb_chunks, api_responses = self.tool_orchestrator.orchestrate(query_analysis)

        logger.info(f"Retrieved: {len(kb_chunks)} KB chunks, {len(api_responses)} API responses")

        # Step 3: Generate response
        response = self.response_generator.generate(
            query=query_analysis['resolved_query'],
            kb_chunks=kb_chunks,
            api_responses=api_responses,
            conversation_history=self.conversation_manager.get_context_for_llm(num_turns=8),
            stream=stream
        )

        # Step 4: Update conversation history
        if not response.get('error'):
            self.conversation_manager.add_turn(
                user_message=query,
                assistant_message=response['text'],
                sources=response.get('sources', []),
                confidence=response.get('confidence')
            )

        logger.info(f"=== Query Processing Complete ===")

        return response

    def process_query_stream(self, query: str) -> Generator[str, None, None]:
        """
        Process query with streaming response.

        Args:
            query: User query

        Yields:
            Response chunks
        """
        logger.info(f"=== Processing Query (Streaming): '{query}' ===")

        # Step 1: Process query
        query_analysis = self.query_processor.process(
            query,
            conversation_context=self.conversation_manager.get_context_for_llm()
        )

        # Step 2: Orchestrate tool execution
        kb_chunks, api_responses = self.tool_orchestrator.orchestrate(query_analysis)

        # Step 3: Stream response
        response_text = []

        for chunk in self.response_generator.generate_stream(
            query=query_analysis['resolved_query'],
            kb_chunks=kb_chunks,
            api_responses=api_responses,
            conversation_history=self.conversation_manager.get_context_for_llm(num_turns=8)
        ):
            response_text.append(chunk)
            yield chunk

        # Step 4: Update conversation history
        full_response = ''.join(response_text)
        sources = self.response_generator.context_builder.extract_sources_from_context(
            kb_chunks=kb_chunks,
            api_responses=api_responses
        )

        self.conversation_manager.add_turn(
            user_message=query,
            assistant_message=full_response,
            sources=sources
        )

        logger.info(f"=== Query Processing Complete (Streaming) ===")

    def get_conversation_history(self) -> list:
        """Get conversation history."""
        return self.conversation_manager.get_history()

    def clear_conversation(self) -> None:
        """Clear conversation history."""
        self.conversation_manager.clear_history()
        logger.info("Conversation cleared")

    def get_stats(self) -> Dict:
        """
        Get agent statistics.

        Returns:
            Dictionary with agent stats
        """
        return {
            'conversation': self.conversation_manager.get_summary(),
            'rate_limit': self.tool_orchestrator.api_orchestrator.get_rate_limit_status(),
            'cache': self.tool_orchestrator.api_orchestrator.get_cache_stats()
        }


# Global crypto agent instance
_crypto_agent = None


def get_crypto_agent() -> CryptoAgent:
    """Get or create global crypto agent instance."""
    global _crypto_agent
    if _crypto_agent is None:
        _crypto_agent = CryptoAgent()
    return _crypto_agent
