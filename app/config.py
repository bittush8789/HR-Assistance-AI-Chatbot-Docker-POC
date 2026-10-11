import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory of the repository (parent of the 'app' directory)
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # OpenAI Configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    # Data & Storage Paths
    documents_dir: Path = BASE_DIR / "data" / "documents"
    chroma_persist_dir: Path = BASE_DIR / "data" / "chroma_db"
    chroma_collection_name: str = "hr_documents"

    # Chunking & Retrieval Parameters
    chunk_size: int = 800
    chunk_overlap: int = 150
    top_k_results: int = 4

    @property
    def is_api_key_set(self) -> bool:
        """Check if a valid, non-placeholder OpenAI API key is set."""
        key = self.openai_api_key.strip()
        return bool(key and key != "your_openai_api_key" and not key.startswith("sk-placeholder"))


settings = Settings()
