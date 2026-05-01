from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Claude (caption generation)
    anthropic_api_key: str = ""

    # Instagram / Meta OAuth
    instagram_app_id: str
    instagram_app_secret: str
    instagram_redirect_uri: str = "http://localhost:8000/auth/instagram/callback"

    # Google Gemini (vision scoring + embeddings)
    google_api_key: str = ""

    # Tavily (trend search - Phase 4+)
    tavily_api_key: str = ""

    # Apify (Instagram scraping - one-time RAG seed)
    apify_api_token: str = ""

    # PostgreSQL
    database_url: str = "postgresql://instagram_agent:password@localhost:5433/instagram_agent"

    # Redis (Celery broker + result backend)
    redis_url: str = "redis://localhost:6379/0"

    # App
    secret_key: str = "change-this-to-a-random-secret-key"
    frontend_url: str = "http://localhost:3000"

    model_config = {"env_file": ".env", "case_sensitive": False, "extra": "ignore"}


settings = Settings()
