"""
ChromaDB manager for vector storage and semantic search.
Handles collection creation, document insertion, and similarity search.
"""

from typing import List, Dict, Optional, Any
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from config.settings import settings
from src.utils.logging_config import logger


class ChromaManager:
    """Manages ChromaDB operations for knowledge base storage."""

    def __init__(self, persist_directory: str = None):
        """
        Initialize ChromaDB client.

        Args:
            persist_directory: Path to persist ChromaDB data
        """
        self.persist_directory = persist_directory or settings.chroma_db_path

        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        logger.info(f"ChromaDB initialized at: {self.persist_directory}")

    def create_collection(
        self,
        name: str,
        embedding_function: Any = None,
        metadata: Dict = None
    ) -> chromadb.Collection:
        """
        Create or get a ChromaDB collection.

        Args:
            name: Collection name
            embedding_function: Custom embedding function (optional)
            metadata: Collection metadata

        Returns:
            ChromaDB collection
        """
        try:
            collection = self.client.get_or_create_collection(
                name=name,
                embedding_function=embedding_function,
                metadata=metadata or {}
            )
            logger.info(f"Collection '{name}' created/retrieved")
            return collection
        except Exception as e:
            logger.error(f"Error creating collection '{name}': {e}")
            raise

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: List[Dict],
        ids: List[str],
        embeddings: Optional[List[List[float]]] = None,
        batch_size: int = 100
    ) -> None:
        """
        Add documents to collection in batches.

        Args:
            collection_name: Name of the collection
            documents: List of document texts
            metadatas: List of metadata dictionaries
            ids: List of unique document IDs
            embeddings: Pre-computed embeddings (optional)
            batch_size: Batch size for insertion
        """
        try:
            collection = self.client.get_collection(name=collection_name)

            total_docs = len(documents)
            logger.info(f"Adding {total_docs} documents to '{collection_name}' in batches of {batch_size}")

            # Add in batches
            for i in range(0, total_docs, batch_size):
                batch_end = min(i + batch_size, total_docs)

                batch_docs = documents[i:batch_end]
                batch_meta = metadatas[i:batch_end]
                batch_ids = ids[i:batch_end]

                if embeddings:
                    batch_emb = embeddings[i:batch_end]
                    collection.add(
                        documents=batch_docs,
                        metadatas=batch_meta,
                        ids=batch_ids,
                        embeddings=batch_emb
                    )
                else:
                    collection.add(
                        documents=batch_docs,
                        metadatas=batch_meta,
                        ids=batch_ids
                    )

                logger.debug(f"Added batch {i//batch_size + 1}: documents {i+1}-{batch_end}")

            logger.info(f"Successfully added {total_docs} documents to '{collection_name}'")

        except Exception as e:
            logger.error(f"Error adding documents to '{collection_name}': {e}")
            raise

    def search(
        self,
        collection_name: str,
        query_texts: List[str] = None,
        query_embeddings: List[List[float]] = None,
        n_results: int = 5,
        where: Dict = None,
        where_document: Dict = None
    ) -> Dict:
        """
        Search for similar documents.

        Args:
            collection_name: Name of the collection
            query_texts: Query texts (will be embedded)
            query_embeddings: Pre-computed query embeddings
            n_results: Number of results to return
            where: Metadata filter
            where_document: Document content filter

        Returns:
            Search results dictionary
        """
        try:
            collection = self.client.get_collection(name=collection_name)

            results = collection.query(
                query_texts=query_texts,
                query_embeddings=query_embeddings,
                n_results=n_results,
                where=where,
                where_document=where_document,
                include=["documents", "metadatas", "distances"]
            )

            logger.debug(f"Search in '{collection_name}' returned {len(results['ids'][0]) if results['ids'] else 0} results")
            return results

        except Exception as e:
            logger.error(f"Error searching in '{collection_name}': {e}")
            raise

    def search_with_threshold(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 5,
        similarity_threshold: float = None,
        metadata_filter: Dict = None
    ) -> List[Dict]:
        """
        Search with similarity threshold filtering.

        Args:
            collection_name: Name of the collection
            query_text: Query string
            n_results: Max number of results
            similarity_threshold: Minimum similarity score (0-1)
            metadata_filter: Filter by metadata

        Returns:
            List of result dictionaries with {id, document, metadata, similarity}
        """
        threshold = similarity_threshold or settings.similarity_threshold

        # Perform search
        results = self.search(
            collection_name=collection_name,
            query_texts=[query_text],
            n_results=n_results,
            where=metadata_filter
        )

        # ChromaDB returns squared L2 distances (lower is more similar)
        # Convert to similarity scores: similarity = 1 - (distance / 2)
        # This maps distance [0, 2] to similarity [1.0, 0.0]
        filtered_results = []

        if results['ids'] and len(results['ids'][0]) > 0:
            for i, doc_id in enumerate(results['ids'][0]):
                distance = results['distances'][0][i]

                # Convert squared L2 distance to similarity score
                # For normalized embeddings, max distance is ~2
                similarity = max(0, 1 - (distance / 2))

                if similarity >= threshold:
                    filtered_results.append({
                        'id': doc_id,
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'similarity': round(similarity, 4),
                        'distance': round(distance, 4)
                    })

        logger.info(f"Found {len(filtered_results)} results above threshold {threshold}")
        return filtered_results

    def get_collection_stats(self, collection_name: str) -> Dict:
        """
        Get statistics about a collection.

        Args:
            collection_name: Name of the collection

        Returns:
            Dictionary with collection stats
        """
        try:
            collection = self.client.get_collection(name=collection_name)

            stats = {
                'name': collection_name,
                'count': collection.count(),
                'metadata': collection.metadata
            }

            logger.debug(f"Collection '{collection_name}' stats: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error getting stats for '{collection_name}': {e}")
            raise

    def delete_collection(self, collection_name: str) -> None:
        """
        Delete a collection.

        Args:
            collection_name: Name of the collection to delete
        """
        try:
            self.client.delete_collection(name=collection_name)
            logger.info(f"Collection '{collection_name}' deleted")
        except Exception as e:
            logger.error(f"Error deleting collection '{collection_name}': {e}")
            raise

    def list_collections(self) -> List[str]:
        """
        List all collections.

        Returns:
            List of collection names
        """
        try:
            collections = self.client.list_collections()
            collection_names = [c.name for c in collections]
            logger.debug(f"Found {len(collection_names)} collections")
            return collection_names
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            raise

    def reset(self) -> None:
        """Reset ChromaDB (delete all collections). Use with caution!"""
        try:
            self.client.reset()
            logger.warning("ChromaDB reset - all collections deleted")
        except Exception as e:
            logger.error(f"Error resetting ChromaDB: {e}")
            raise


# Global ChromaDB manager instance
_chroma_manager = None


def get_chroma_manager() -> ChromaManager:
    """Get or create global ChromaDB manager instance."""
    global _chroma_manager
    if _chroma_manager is None:
        _chroma_manager = ChromaManager()
    return _chroma_manager
