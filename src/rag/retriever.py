"""
Semantic search retriever using ChromaDB.
Retrieves relevant knowledge base chunks for user queries.
"""

from typing import List, Dict, Optional
from src.knowledge_base.chroma_manager import get_chroma_manager
from src.core.embeddings import get_embedding_manager
from config.settings import settings
from src.utils.logging_config import logger


class Retriever:
    """Semantic search retriever for knowledge base."""

    def __init__(self, collection_name: str = "crypto_knowledge"):
        """
        Initialize retriever.

        Args:
            collection_name: ChromaDB collection name
        """
        self.collection_name = collection_name
        self.chroma_manager = get_chroma_manager()
        self.embedding_manager = get_embedding_manager()

        logger.info(f"Retriever initialized for collection: {collection_name}")

    def retrieve(
        self,
        query: str,
        top_k: int = None,
        similarity_threshold: float = None,
        category_filter: str = None
    ) -> List[Dict]:
        """
        Retrieve relevant documents for a query.

        Args:
            query: User query
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score
            category_filter: Filter by category (e.g., 'Bitcoin', 'DeFi')

        Returns:
            List of retrieved documents with metadata
        """
        top_k = top_k or settings.top_k_results
        similarity_threshold = similarity_threshold or settings.similarity_threshold

        logger.info(f"Retrieving documents for query: '{query[:50]}...'")

        # Build metadata filter
        metadata_filter = None
        if category_filter:
            metadata_filter = {'category': category_filter}

        # Perform search
        results = self.chroma_manager.search_with_threshold(
            collection_name=self.collection_name,
            query_text=query,
            n_results=top_k,
            similarity_threshold=similarity_threshold,
            metadata_filter=metadata_filter
        )

        logger.info(f"Retrieved {len(results)} documents above threshold {similarity_threshold}")

        return results

    def retrieve_by_entity(
        self,
        entity: str,
        top_k: int = None,
        similarity_threshold: float = None
    ) -> List[Dict]:
        """
        Retrieve documents related to a specific entity.

        Args:
            entity: Entity name (e.g., 'Bitcoin', 'Ethereum')
            top_k: Number of results
            similarity_threshold: Minimum similarity

        Returns:
            List of retrieved documents
        """
        # Use entity as query
        query = f"What is {entity}?"

        return self.retrieve(
            query=query,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )

    def retrieve_multiple_queries(
        self,
        queries: List[str],
        top_k: int = None,
        similarity_threshold: float = None
    ) -> Dict[str, List[Dict]]:
        """
        Retrieve documents for multiple queries.

        Args:
            queries: List of queries
            top_k: Number of results per query
            similarity_threshold: Minimum similarity

        Returns:
            Dictionary mapping queries to results
        """
        results = {}

        for query in queries:
            results[query] = self.retrieve(
                query=query,
                top_k=top_k,
                similarity_threshold=similarity_threshold
            )

        return results

    def check_relevance(self, query: str, threshold: float = None) -> bool:
        """
        Check if KB has relevant information for query.

        Args:
            query: User query
            threshold: Similarity threshold

        Returns:
            True if relevant documents found
        """
        threshold = threshold or settings.similarity_threshold

        results = self.retrieve(query=query, top_k=1, similarity_threshold=threshold)

        has_relevant = len(results) > 0

        logger.info(f"Relevance check for '{query[:50]}...': {has_relevant}")

        return has_relevant


# Global retriever instance
_retriever = None


def get_retriever() -> Retriever:
    """Get or create global retriever instance."""
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever
