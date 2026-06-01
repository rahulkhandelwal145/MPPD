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
    groq_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
    )


settings = Settings()
