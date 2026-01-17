"""
Metadata store for tracking knowledge base versions and statistics.
Uses SQLite for persistent storage.
"""

import sqlite3
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path
from config.settings import settings
from src.utils.logging_config import logger


class MetadataStore:
    """Manages knowledge base metadata in SQLite."""

    def __init__(self, db_path: str = None):
        """
        Initialize metadata store.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path or settings.sqlite_db_path

        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_db()
        logger.info(f"Metadata store initialized at: {self.db_path}")

    def _init_db(self):
        """Initialize database schema (if not exists)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # KB metadata table (created in cache_manager, but ensure it exists)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kb_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kb_version TEXT NOT NULL,
                total_documents INTEGER,
                total_chunks INTEGER,
                embedding_model TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def save_kb_metadata(
        self,
        kb_version: str,
        total_documents: int,
        total_chunks: int,
        embedding_model: str
    ) -> int:
        """
        Save knowledge base metadata.

        Args:
            kb_version: Version identifier
            total_documents: Number of documents
            total_chunks: Number of chunks
            embedding_model: Embedding model used

        Returns:
            Metadata record ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO kb_metadata
            (kb_version, total_documents, total_chunks, embedding_model)
            VALUES (?, ?, ?, ?)
        """, (kb_version, total_documents, total_chunks, embedding_model))

        metadata_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"Saved KB metadata (ID: {metadata_id}, version: {kb_version})")
        return metadata_id

    def get_latest_kb_metadata(self) -> Optional[Dict]:
        """
        Get the most recent knowledge base metadata.

        Returns:
            Metadata dictionary or None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, kb_version, total_documents, total_chunks,
                   embedding_model, created_at, updated_at
            FROM kb_metadata
            ORDER BY created_at DESC
            LIMIT 1
        """)

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'id': row[0],
                'kb_version': row[1],
                'total_documents': row[2],
                'total_chunks': row[3],
                'embedding_model': row[4],
                'created_at': row[5],
                'updated_at': row[6]
            }

        return None

    def update_kb_metadata(self, metadata_id: int) -> None:
        """
        Update the 'updated_at' timestamp for a metadata record.

        Args:
            metadata_id: ID of the metadata record
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE kb_metadata
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (metadata_id,))

        conn.commit()
        conn.close()

        logger.debug(f"Updated KB metadata (ID: {metadata_id})")


# Global metadata store instance
_metadata_store = None


def get_metadata_store() -> MetadataStore:
    """Get or create global metadata store instance."""
    global _metadata_store
    if _metadata_store is None:
        _metadata_store = MetadataStore()
    return _metadata_store
