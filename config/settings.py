"""
Centralized configuration management using Pydantic.
Loads environment variables and validates settings.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the project root directory (parent of config folder)
PROJECT_ROOT = Path(__file__).parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    gemini_api_key: str = Field(..., alias="GEMINI_API_KEY")

    # Paths (Windows-compatible)
    chroma_db_path: str = Field(
        default="c:/Agentic AI SMIT/Projects/cyrpto agent/data/chromadb",
        alias="CHROMA_DB_PATH"
    )
    sqlite_db_path: str = Field(
        default="c:/Agentic AI SMIT/Projects/cyrpto agent/data/sqlite/metadata.db",
        alias="SQLITE_DB_PATH"
    )

    # Model Settings
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        alias="EMBEDDING_MODEL"
    )
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")
    temperature: float = Field(default=0.1, alias="TEMPERATURE")
    max_tokens: int = Field(default=2048, alias="MAX_TOKENS")

    # RAG Settings
    similarity_threshold: float = Field(default=0.5, alias="SIMILARITY_THRESHOLD")
    top_k_results: int = Field(default=5, alias="TOP_K_RESULTS")
    chunk_size: int = Field(default=1000, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, alias="CHUNK_OVERLAP")

    # Cache Settings (TTL in seconds)
    price_cache_ttl: int = Field(default=60, alias="PRICE_CACHE_TTL")
    historical_cache_ttl: int = Field(default=3600, alias="HISTORICAL_CACHE_TTL")
    technical_cache_ttl: int = Field(default=300, alias="TECHNICAL_CACHE_TTL")

    # Rate Limiting
    freecrypto_monthly_limit: int = Field(default=100000, alias="FREECRYPTO_MONTHLY_LIMIT")
    gemini_rpm_limit: int = Field(default=60, alias="GEMINI_RPM_LIMIT")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @field_validator("similarity_threshold")
    @classmethod
    def validate_similarity_threshold(cls, v: float) -> float:
        """Ensure similarity threshold is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("Similarity threshold must be between 0 and 1")
        return v

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Ensure temperature is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("Temperature must be between 0 and 1")
        return v

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        Path(self.chroma_db_path).mkdir(parents=True, exist_ok=True)
        Path(self.sqlite_db_path).parent.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()

# Ensure directories exist
settings.ensure_directories()
