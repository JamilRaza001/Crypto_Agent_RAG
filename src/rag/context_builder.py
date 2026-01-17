"""
Context builder - assembles context from KB chunks, API data, and conversation history.
Formats context for LLM consumption with proper source attribution.
"""

from typing import List, Dict, Optional
from datetime import datetime
from config.prompts import format_kb_source, format_api_source
from src.utils.logging_config import logger


class ContextBuilder:
    """Builds LLM context from multiple sources."""

    def __init__(self, max_context_length: int = 4000):
        """
        Initialize context builder.

        Args:
            max_context_length: Maximum context length in tokens (approximate)
        """
        self.max_context_length = max_context_length
        logger.info(f"Context builder initialized (max length: {max_context_length} tokens)")

    def build_kb_context(self, kb_chunks: List[Dict]) -> str:
        """
        Build context string from KB chunks.

        Args:
            kb_chunks: List of KB chunk dictionaries

        Returns:
            Formatted KB context string
        """
        if not kb_chunks:
            return ""

        context_parts = ["=== Knowledge Base Sources ===\n"]

        for i, chunk in enumerate(kb_chunks, 1):
            title = chunk['metadata'].get('title', 'Unknown')
            content = chunk['document']
            similarity = chunk.get('similarity', chunk.get('rerank_score', 0))

            source = format_kb_source(title, content, similarity)
            context_parts.append(f"{source}\n")

        return "\n".join(context_parts)

    def build_api_context(self, api_responses: List[Dict]) -> str:
        """
        Build context string from API responses.

        Args:
            api_responses: List of API response dictionaries

        Returns:
            Formatted API context string
        """
        if not api_responses:
            return ""

        context_parts = ["=== API Data Sources ===\n"]

        for response in api_responses:
            endpoint = response.get('endpoint', 'Unknown')
            data = response.get('data', {})
            timestamp = response.get('timestamp', datetime.utcnow().isoformat())

            source = format_api_source(endpoint, data, timestamp)
            context_parts.append(f"{source}\n")

        return "\n".join(context_parts)

    def build_conversation_context(self, conversation_history: List[Dict]) -> str:
        """
        Build context string from conversation history.

        Args:
            conversation_history: List of conversation turn dictionaries

        Returns:
            Formatted conversation context
        """
        if not conversation_history:
            return ""

        context_parts = ["=== Conversation History ===\n"]

        for turn in conversation_history:
            role = turn.get('role', 'unknown').upper()
            content = turn.get('content', '')
            context_parts.append(f"{role}: {content}\n")

        context_parts.append("\nNote: Use conversation history for entity resolution and context, but do NOT cite it as a source.\n")

        return "\n".join(context_parts)

    def build_full_context(
        self,
        query: str,
        kb_chunks: List[Dict] = None,
        api_responses: List[Dict] = None,
        conversation_history: List[Dict] = None
    ) -> str:
        """
        Build complete context for LLM.

        Args:
            query: User query
            kb_chunks: Knowledge base chunks
            api_responses: API response data
            conversation_history: Conversation history

        Returns:
            Complete formatted context string
        """
        context_parts = []

        # Query
        context_parts.append(f"User Query: {query}\n")

        # KB context
        if kb_chunks:
            kb_context = self.build_kb_context(kb_chunks)
            context_parts.append(kb_context)
            logger.info(f"Added {len(kb_chunks)} KB chunks to context")

        # API context
        if api_responses:
            api_context = self.build_api_context(api_responses)
            context_parts.append(api_context)
            logger.info(f"Added {len(api_responses)} API responses to context")

        # Conversation context
        if conversation_history:
            conv_context = self.build_conversation_context(conversation_history)
            context_parts.append(conv_context)
            logger.info(f"Added {len(conversation_history)} conversation turns to context")

        full_context = "\n".join(context_parts)

        # Estimate token count (rough: ~4 chars per token)
        estimated_tokens = len(full_context) // 4

        if estimated_tokens > self.max_context_length:
            logger.warning(f"Context exceeds max length: {estimated_tokens} > {self.max_context_length} tokens")
            # Truncate if needed (prioritize KB and API over conversation)
            # For now, just log warning
        else:
            logger.info(f"Context built successfully (~{estimated_tokens} tokens)")

        return full_context

    def extract_sources_from_context(
        self,
        kb_chunks: List[Dict] = None,
        api_responses: List[Dict] = None
    ) -> List[Dict]:
        """
        Extract source information for citation display.

        Args:
            kb_chunks: KB chunks used
            api_responses: API responses used

        Returns:
            List of source dictionaries
        """
        sources = []

        # KB sources
        if kb_chunks:
            for chunk in kb_chunks:
                sources.append({
                    'type': 'knowledge_base',
                    'title': chunk['metadata'].get('title', 'Unknown'),
                    'category': chunk['metadata'].get('category', 'Unknown'),
                    'similarity': chunk.get('similarity', chunk.get('rerank_score', 0)),
                    'content_preview': chunk['document'][:150] + '...'
                })

        # API sources
        if api_responses:
            for response in api_responses:
                sources.append({
                    'type': 'api',
                    'endpoint': response.get('endpoint', 'Unknown'),
                    'timestamp': response.get('timestamp', ''),
                    'data_preview': str(response.get('data', {}))[:150] + '...'
                })

        return sources


# Global context builder instance
_context_builder = None


def get_context_builder() -> ContextBuilder:
    """Get or create global context builder instance."""
    global _context_builder
    if _context_builder is None:
        _context_builder = ContextBuilder()
    return _context_builder
