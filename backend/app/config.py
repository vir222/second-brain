from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url : str
    jwt_secret : str
    jwt_algorithm : str = "HS256"
    access_token_expire_minutes : int = 60
    model_config = SettingsConfigDict(env_file=".env")
    cors_origins : list[str] = ["http://localhost:3000"]
    upload_dir : str = "uploads"
    max_upload_mb: int = 20  
    redis_url : str = "redis://localhost:6379/0"
    openai_api_key : str
    embedding_model : str = "text-embedding-3-small"
    anthropic_api_key : str
    chat_model : str = "claude-haiku-5-5"
    rag_top_k : int = 6
    min_relevance_score : float = 0.3
    environment: str = "development"
    rate_limit_enabled: bool = True
settings = Settings()