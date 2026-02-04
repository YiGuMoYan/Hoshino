from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "Hoshino"
    OPENAI_API_KEY: str = "sk-..."
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    
    # TMDB API Configuration
    TMDB_API_KEY: str = ""  # Get from https://www.themoviedb.org/settings/api
    TMDB_BASE_URL: str = "https://api.themoviedb.org/3"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
