"""
Script to add new data to the knowledge base without rebuilding everything.
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.knowledge_base.kb_initializer import KBInitializer
from src.utils.logging_config import logger


def add_new_document(category: str, title: str, content: str, metadata: dict = None):
    """
    Add a new document to the knowledge base.

    Args:
        category: Document category
        title: Document title
        content: Document content
        metadata: Additional metadata
    """
    print(f"Adding new document: {title}")

    initializer = KBInitializer()

    # Create document structure
    document = {
        'id': f"{category.lower()}_{title.lower().replace(' ', '_')}",
        'title': title,
        'content': content,
        'category': category,
        'metadata': metadata or {}
    }

    # Chunk and prepare
    chunk_texts, chunk_metadatas, chunk_ids = initializer.prepare_documents_for_indexing([document])

    # Generate embeddings
    print(f"Generating embeddings for {len(chunk_texts)} chunks...")
    embeddings = initializer.embedding_manager.embed_batch(chunk_texts)

    # Add to collection
    print(f"Adding to collection '{initializer.collection_name}'...")
    initializer.chroma_manager.add_documents(
        collection_name=initializer.collection_name,
        documents=chunk_texts,
        metadatas=chunk_metadatas,
        ids=chunk_ids,
        embeddings=embeddings.tolist()
    )

    print(f"✅ Added {len(chunk_texts)} chunks to knowledge base")

    # Test search for the new document
    print(f"\nTesting search for new document...")
    results = initializer.chroma_manager.search_with_threshold(
        collection_name=initializer.collection_name,
        query_text=title,
        n_results=1
    )

    if results:
        print(f"✅ Document searchable (similarity: {results[0]['similarity']:.4f})")
    else:
        print("⚠️  Document may not be searchable")


def main():
    """Main entry point for adding KB data."""
    print("=" * 70)
    print("Add New Knowledge Base Data")
    print("=" * 70)
    print()

    # Example: Add a new document about Layer 2 solutions
    print("Example: Adding document about Polygon")
    print()

    add_new_document(
        category="Layer 2",
        title="Polygon Network",
        content="""Polygon (formerly Matic Network) is a Layer 2 scaling solution for Ethereum.
        It provides a framework for building and connecting Ethereum-compatible blockchain networks.
        Polygon uses a Proof of Stake consensus mechanism and offers fast, low-cost transactions.
        The network is secured by a set of validators who stake MATIC tokens. Polygon has become
        one of the most popular scaling solutions, hosting thousands of dApps including major DeFi
        protocols and NFT marketplaces. It offers multiple scaling solutions including Polygon PoS
        (the main chain), Polygon zkEVM (zero-knowledge rollup), and Polygon CDK for custom chains.
        Transaction fees on Polygon are typically fractions of a cent, compared to dollars on Ethereum mainnet.""",
        metadata={
            'source': 'Polygon Documentation',
            'entities': ['Polygon', 'MATIC', 'Layer 2', 'scaling', 'PoS']
        }
    )

    print("\n" + "=" * 70)
    print("To add your own documents:")
    print("=" * 70)
    print()
    print("1. Edit this script to include your new content")
    print("2. Or add JSON files to data/knowledge_base/raw/")
    print("3. Then run: python scripts/init_kb.py --reset")
    print()


if __name__ == "__main__":
    main()
