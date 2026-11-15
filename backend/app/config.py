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
settings = Settings()