from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    datagov_api_key: str | None = None
    scraper_delay_seconds: float = 1.5
    scraper_cache_dir: str = "./data/cache"
    scraper_user_agent: str = "MPScorer-Civic-Research/1.0"
    debug: bool = False
    anthropic_api_key: str | None = None
    # LLM extraction provider: "groq" (cloud, token-capped) or "ollama" (local).
    llm_provider: str = "groq"
    groq_api_key: str | None = None
    groq_model: str = "llama-3.1-8b-instant"
    groq_classification_model: str = "llama-3.3-70b-versatile"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
    )


settings = Settings()
