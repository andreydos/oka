from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://oka:oka@localhost:5432/oka"
    qdrant_url: str = "http://localhost:6333"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    embedding_model: str = "nomic-embed-text"
    upload_dir: str = "./data/uploads"
    relevance_threshold: float = 0.5
    min_relevance_score: float = 0.54
    relevance_relative_gap: float = 0.05
    max_context_chunks: int = 5
    max_citations: int = 5
    llm_provider: str = "ollama"
    ml_mutex_enabled: bool = True
    top_k: int = 5
    chunk_size: int = 320
    chunk_overlap: int = 48
    vector_size: int = 768
    qdrant_collection: str = "knowledge_chunks"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    tesseract_cmd: str = "tesseract"
    ocr_language: str = "eng"


settings = Settings()
