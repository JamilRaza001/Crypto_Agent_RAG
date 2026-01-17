"""
Knowledge Base initialization script.
Run this to populate ChromaDB with cryptocurrency knowledge.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.knowledge_base.kb_initializer import KBInitializer
from src.knowledge_base.metadata_store import get_metadata_store
from src.utils.logging_config import logger


def main():
    """Initialize the knowledge base."""
    print("=" * 70)
    print("Cryptocurrency Knowledge Base Initialization")
    print("=" * 70)
    print()

    # Check if we should reset
    reset = False
    if len(sys.argv) > 1 and sys.argv[1] == '--reset':
        reset = True
        print("⚠️  WARNING: Resetting existing knowledge base")
        response = input("Are you sure? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted")
            return

    try:
        # Initialize KB
        initializer = KBInitializer()
        stats = initializer.initialize_kb(reset=reset)

        print("\n" + "=" * 70)
        print("Knowledge Base Initialization Complete!")
        print("=" * 70)
        print()
        print(f"📚 Total Documents: {stats['total_documents']}")
        print(f"📄 Total Chunks: {stats['total_chunks']}")
        print(f"🔢 Embedding Dimension: {stats['embedding_dimension']}")
        print()
        print("Category Breakdown:")
        for category, count in stats['category_breakdown'].items():
            print(f"  - {category}: {count} chunks")
        print()

        # Save metadata
        metadata_store = get_metadata_store()
        metadata_store.save_kb_metadata(
            kb_version="1.0.0",
            total_documents=stats['total_documents'],
            total_chunks=stats['total_chunks'],
            embedding_model=stats['metadata']['embedding_model']
        )

        # Test search
        print("=" * 70)
        print("Testing Knowledge Base Search")
        print("=" * 70)
        print()

        test_queries = [
            "What is Bitcoin?",
            "Explain Ethereum smart contracts",
            "What is DeFi?"
        ]

        for query in test_queries:
            print(f"\n🔍 Query: '{query}'")
            print("-" * 70)

            results = initializer.chroma_manager.search_with_threshold(
                collection_name=initializer.collection_name,
                query_text=query,
                n_results=2
            )

            if results:
                for i, result in enumerate(results, 1):
                    print(f"\nResult {i} (Similarity: {result['similarity']:.4f}):")
                    print(f"Title: {result['metadata'].get('title', 'Unknown')}")
                    print(f"Category: {result['metadata'].get('category', 'Unknown')}")
                    print(f"Content: {result['document'][:150]}...")
            else:
                print("No results found")

        print("\n" + "=" * 70)
        print("✅ Knowledge Base Ready!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("1. Continue with Phase 4: API Integration")
        print("2. Test search: python -c \"from src.knowledge_base.kb_initializer import KBInitializer; KBInitializer().test_search()\"")
        print()

    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ Error during initialization")
        print("=" * 70)
        print(f"\nError: {e}")
        logger.exception("Knowledge base initialization failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
