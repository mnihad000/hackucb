from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DEMO_MODE: bool = True

    # Real integration keys — unused in demo mode, swapped in later
    ANTHROPIC_API_KEY: str = ""
    REDIS_URL: str = "redis://localhost:6379"
    BROWSERBASE_API_KEY: str = ""
    ARIZE_API_KEY: str = ""
    ARIZE_SPACE_KEY: str = ""
    TAVILY_API_KEY: str = ""
    SERPAPI_API_KEY: str = ""
    SEARCH_PROVIDER: str = "tavily"
    INVESTIGATION_DB_PATH: str = "investigations.sqlite3"
    RETRIEVER_MAX_ROUNDS: int = 3
    RETRIEVER_MAX_RESULTS_PER_QUERY: int = 5
    FETCH_TIMEOUT_SECONDS: int = 20

    # GDELT — no key required, free public API
    GDELT_MAX_RECORDS: int = 50
    GDELT_BASE_URL: str = "https://api.gdeltproject.org/api/v2/doc/doc"

    # Hacker News (Algolia) — no key required, free public API
    HN_SEARCH_URL: str = "https://hn.algolia.com/api/v1/search"
    HN_DEFAULT_RESULTS: int = 50

    SPIKE_WINDOW_DAYS: int = 6
    MUTATION_SIMILARITY_LOW: float = 0.40
    MUTATION_SIMILARITY_HIGH: float = 0.85
    ENTITY_OVERLAP_WINDOW_HOURS: int = 72


@lru_cache
def get_settings() -> Settings:
    return Settings()
