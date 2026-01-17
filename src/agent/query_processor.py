"""
Query processor - classifies user queries and extracts entities.
Determines routing strategy (KB vs API vs both).
"""

from typing import Dict, List, Tuple
from src.knowledge_base.entity_resolver import get_entity_resolver
from src.utils.logging_config import logger


class QueryProcessor:
    """Processes and classifies user queries."""

    def __init__(self):
        """Initialize query processor."""
        self.entity_resolver = get_entity_resolver()

        # Query type patterns
        self.price_patterns = [
            'price', 'cost', 'worth', 'value', 'trading at', 'current',
            'how much', 'market cap', 'market capitalization'
        ]

        self.technical_patterns = [
            'rsi', 'macd', 'moving average', 'bollinger', 'technical',
            'indicator', 'analysis', 'chart', 'trend'
        ]

        self.historical_patterns = [
            'history', 'historical', 'past', 'previous', 'ago',
            'yesterday', 'last week', 'last month', 'chart'
        ]

        self.conceptual_patterns = [
            'what is', 'what are', 'explain', 'how does', 'how do',
            'why', 'definition', 'meaning', 'tell me about', 'describe'
        ]

        logger.info("Query processor initialized")

    def classify_query(self, query: str) -> str:
        """
        Classify query type.

        Args:
            query: User query

        Returns:
            Query type: 'conceptual', 'real-time', 'technical', 'historical', 'general'
        """
        query_lower = query.lower()

        # Check for conceptual queries
        if any(pattern in query_lower for pattern in self.conceptual_patterns):
            logger.info("Query classified as: conceptual")
            return 'conceptual'

        # Check for technical analysis queries
        if any(pattern in query_lower for pattern in self.technical_patterns):
            logger.info("Query classified as: technical")
            return 'technical'

        # Check for historical queries
        if any(pattern in query_lower for pattern in self.historical_patterns):
            logger.info("Query classified as: historical")
            return 'historical'

        # Check for price/real-time queries
        if any(pattern in query_lower for pattern in self.price_patterns):
            logger.info("Query classified as: real-time")
            return 'real-time'

        # Default to general
        logger.info("Query classified as: general")
        return 'general'

    def extract_crypto_symbols(self, query: str) -> List[str]:
        """
        Extract cryptocurrency symbols from query.

        Args:
            query: User query

        Returns:
            List of crypto symbols
        """
        symbols = []
        entities = self.entity_resolver.extract_entities(query)

        for entity in entities:
            # Normalize to symbol
            normalized = self.entity_resolver.normalize_entity(entity)
            symbols.append(normalized)

        logger.info(f"Extracted symbols: {symbols}")
        return symbols

    def resolve_query(self, query: str, conversation_context: List[Dict] = None) -> str:
        """
        Resolve pronouns and ambiguous references in query.

        Args:
            query: User query
            conversation_context: Previous conversation turns

        Returns:
            Resolved query
        """
        # Check if contains pronouns
        if self.entity_resolver.contains_pronoun(query):
            resolved = self.entity_resolver.resolve_pronouns(query)
            logger.info(f"Resolved query: '{query}' -> '{resolved}'")
            return resolved

        return query

    def process(self, query: str, conversation_context: List[Dict] = None) -> Dict:
        """
        Process query completely.

        Args:
            query: User query
            conversation_context: Conversation history

        Returns:
            Dictionary with query analysis
        """
        logger.info(f"Processing query: '{query}'")

        # Resolve pronouns
        resolved_query = self.resolve_query(query, conversation_context)

        # Classify query type
        query_type = self.classify_query(resolved_query)

        # Extract entities/symbols
        symbols = self.extract_crypto_symbols(resolved_query)
        entities = list(self.entity_resolver.extract_entities(resolved_query))

        result = {
            'original_query': query,
            'resolved_query': resolved_query,
            'query_type': query_type,
            'symbols': symbols,
            'entities': entities,
            'needs_kb': query_type in ['conceptual', 'general', 'technical'],
            'needs_api': query_type in ['real-time', 'technical', 'historical']
        }

        logger.info(f"Query processed: type={query_type}, needs_kb={result['needs_kb']}, needs_api={result['needs_api']}")

        return result


# Global query processor instance
_query_processor = None


def get_query_processor() -> QueryProcessor:
    """Get or create global query processor instance."""
    global _query_processor
    if _query_processor is None:
        _query_processor = QueryProcessor()
    return _query_processor
