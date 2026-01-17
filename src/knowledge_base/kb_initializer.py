"""
Knowledge Base initialization - loads, chunks, and indexes crypto knowledge.
"""

import json
from pathlib import Path
from typing import List, Dict, Tuple
from config.settings import settings
from src.core.embeddings import get_embedding_manager
from src.knowledge_base.chroma_manager import get_chroma_manager
from src.utils.logging_config import logger


class KBInitializer:
    """Initialize and populate the knowledge base."""

    def __init__(self):
        """Initialize KB components."""
        self.embedding_manager = get_embedding_manager()
        self.chroma_manager = get_chroma_manager()
        self.kb_data_path = Path("data/knowledge_base/raw")
        self.collection_name = "crypto_knowledge"

    def load_kb_files(self) -> List[Dict]:
        """
        Load all JSON knowledge base files.

        Returns:
            List of all documents with metadata
        """
        all_documents = []

        json_files = list(self.kb_data_path.glob("*.json"))

        if not json_files:
            raise FileNotFoundError(f"No JSON files found in {self.kb_data_path}")

        logger.info(f"Loading {len(json_files)} knowledge base files")

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                category = data.get('category', 'Unknown')
                documents = data.get('documents', [])

                logger.info(f"Loaded {len(documents)} documents from {json_file.name} (category: {category})")

                # Add category to each document
                for doc in documents:
                    doc['category'] = category
                    all_documents.append(doc)

            except Exception as e:
                logger.error(f"Error loading {json_file}: {e}")
                raise

        logger.info(f"Total documents loaded: {len(all_documents)}")
        return all_documents

    def chunk_document(self, content: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """
        Split document into overlapping chunks.

        Args:
            content: Document text
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks

        Returns:
            List of text chunks
        """
        chunk_size = chunk_size or settings.chunk_size
        overlap = overlap or settings.chunk_overlap

        if len(content) <= chunk_size:
            return [content]

        chunks = []
        start = 0

        while start < len(content):
            end = start + chunk_size

            # Try to break at sentence or word boundary
            if end < len(content):
                # Look for sentence end
                sentence_end = content.rfind('. ', start, end)
                if sentence_end != -1 and sentence_end > start + chunk_size // 2:
                    end = sentence_end + 1
                else:
                    # Look for word boundary
                    space = content.rfind(' ', start, end)
                    if space != -1 and space > start + chunk_size // 2:
                        end = space

            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start position with overlap
            start = end - overlap if end < len(content) else len(content)

        return chunks

    def prepare_documents_for_indexing(self, documents: List[Dict]) -> Tuple[List[str], List[Dict], List[str]]:
        """
        Chunk documents and prepare for ChromaDB indexing.

        Args:
            documents: List of document dictionaries

        Returns:
            Tuple of (chunk_texts, chunk_metadatas, chunk_ids)
        """
        chunk_texts = []
        chunk_metadatas = []
        chunk_ids = []

        logger.info(f"Chunking {len(documents)} documents...")

        for doc in documents:
            content = doc.get('content', '')
            doc_id = doc.get('id', 'unknown')
            title = doc.get('title', 'Untitled')
            category = doc.get('category', 'Unknown')
            metadata = doc.get('metadata', {})

            # Chunk the document
            chunks = self.chunk_document(content)

            # Create chunk records
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{i}"

                chunk_metadata = {
                    'document_id': doc_id,
                    'title': title,
                    'category': category,
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'source': metadata.get('source', 'Unknown'),
                }

                # Add entities if present
                if 'entities' in metadata:
                    chunk_metadata['entities'] = ','.join(metadata['entities'])

                chunk_texts.append(chunk)
                chunk_metadatas.append(chunk_metadata)
                chunk_ids.append(chunk_id)

        logger.info(f"Created {len(chunk_texts)} chunks from {len(documents)} documents")
        return chunk_texts, chunk_metadatas, chunk_ids

    def initialize_kb(self, reset: bool = False) -> Dict:
        """
        Initialize the knowledge base by loading, chunking, and indexing documents.

        Args:
            reset: Whether to reset existing collection

        Returns:
            Dictionary with initialization stats
        """
        logger.info("Starting knowledge base initialization...")

        # Reset if requested
        if reset:
            logger.warning("Resetting existing knowledge base...")
            try:
                self.chroma_manager.delete_collection(self.collection_name)
            except Exception:
                pass  # Collection might not exist

        # Load documents
        documents = self.load_kb_files()

        # Prepare chunks
        chunk_texts, chunk_metadatas, chunk_ids = self.prepare_documents_for_indexing(documents)

        # Generate embeddings
        logger.info(f"Generating embeddings for {len(chunk_texts)} chunks...")
        embeddings = self.embedding_manager.embed_batch(
            chunk_texts,
            batch_size=32,
            show_progress=True
        )

        # Create collection
        logger.info(f"Creating collection '{self.collection_name}'...")
        collection = self.chroma_manager.create_collection(
            name=self.collection_name,
            metadata={
                'description': 'Cryptocurrency and blockchain knowledge base',
                'embedding_model': settings.embedding_model,
                'chunk_size': settings.chunk_size,
                'chunk_overlap': settings.chunk_overlap
            }
        )

        # Add documents to collection
        logger.info("Indexing documents in ChromaDB...")
        self.chroma_manager.add_documents(
            collection_name=self.collection_name,
            documents=chunk_texts,
            metadatas=chunk_metadatas,
            ids=chunk_ids,
            embeddings=embeddings.tolist(),
            batch_size=100
        )

        # Get stats
        stats = self.chroma_manager.get_collection_stats(self.collection_name)

        # Add category breakdown
        category_counts = {}
        for meta in chunk_metadatas:
            cat = meta.get('category', 'Unknown')
            category_counts[cat] = category_counts.get(cat, 0) + 1

        stats['category_breakdown'] = category_counts
        stats['total_documents'] = len(documents)
        stats['total_chunks'] = len(chunk_texts)
        stats['embedding_dimension'] = self.embedding_manager.get_dimension()

        logger.info(f"Knowledge base initialization complete!")
        logger.info(f"Stats: {stats}")

        return stats

    def test_search(self, query: str = "What is Bitcoin?", top_k: int = 3) -> None:
        """
        Test knowledge base search.

        Args:
            query: Test query
            top_k: Number of results to return
        """
        logger.info(f"\nTesting search with query: '{query}'")

        results = self.chroma_manager.search_with_threshold(
            collection_name=self.collection_name,
            query_text=query,
            n_results=top_k
        )

        if not results:
            logger.warning("No results found!")
            return

        logger.info(f"Found {len(results)} results:\n")

        for i, result in enumerate(results, 1):
            logger.info(f"Result {i}:")
            logger.info(f"  Title: {result['metadata'].get('title', 'Unknown')}")
            logger.info(f"  Category: {result['metadata'].get('category', 'Unknown')}")
            logger.info(f"  Similarity: {result['similarity']:.4f}")
            logger.info(f"  Content: {result['document'][:200]}...")
            logger.info("")


# Helper function for easy initialization
def initialize_knowledge_base(reset: bool = False) -> Dict:
    """
    Initialize the knowledge base.

    Args:
        reset: Whether to reset existing data

    Returns:
        Initialization statistics
    """
    initializer = KBInitializer()
    return initializer.initialize_kb(reset=reset)
