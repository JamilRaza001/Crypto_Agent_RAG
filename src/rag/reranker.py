"""
Re-ranking module using cross-encoder for improved retrieval accuracy.
Cross-encoders provide better relevance scoring than bi-encoders.
"""

from typing import List, Dict
from sentence_transformers import CrossEncoder
from src.utils.logging_config import logger


class Reranker:
    """Re-ranks retrieved documents using cross-encoder."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Initialize re-ranker.

        Args:
            model_name: Cross-encoder model name
        """
        self.model_name = model_name

        logger.info(f"Loading cross-encoder model: {model_name}")

        try:
            self.model = CrossEncoder(model_name)
            logger.info("Cross-encoder loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load cross-encoder: {e}")
            logger.warning("Re-ranking will be disabled")
            self.model = None

    def rerank(
        self,
        query: str,
        documents: List[Dict],
        top_k: int = None
    ) -> List[Dict]:
        """
        Re-rank documents using cross-encoder.

        Args:
            query: User query
            documents: List of document dictionaries with 'document' field
            top_k: Number of top documents to return (None = all)

        Returns:
            Re-ranked list of documents with updated scores
        """
        if not documents:
            return documents

        if self.model is None:
            logger.warning("Cross-encoder not available, skipping re-ranking")
            return documents

        logger.info(f"Re-ranking {len(documents)} documents")

        try:
            # Prepare query-document pairs
            pairs = [[query, doc['document']] for doc in documents]

            # Get cross-encoder scores
            scores = self.model.predict(pairs)

            # Add scores to documents
            for i, doc in enumerate(documents):
                doc['rerank_score'] = float(scores[i])
                # Keep original similarity score as well
                doc['original_similarity'] = doc.get('similarity', 0.0)

            # Sort by rerank score (descending)
            reranked = sorted(documents, key=lambda x: x['rerank_score'], reverse=True)

            # Return top_k if specified
            if top_k:
                reranked = reranked[:top_k]

            logger.info(f"Re-ranking complete. Top score: {reranked[0]['rerank_score']:.4f}")

            return reranked

        except Exception as e:
            logger.error(f"Error during re-ranking: {e}")
            return documents


# Global re-ranker instance
_reranker = None


def get_reranker() -> Reranker:
    """Get or create global re-ranker instance."""
    global _reranker
    if _reranker is None:
        _reranker = Reranker()
    return _reranker
