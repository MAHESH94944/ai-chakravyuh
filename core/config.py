# core/config.py
"""Application settings with enhanced API configuration for multiple data sources."""

from typing import Optional
import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Load variables from the .env file
    # Allow extra environment variables (for example external services that use
    # different key names like `mongodb_uri`) so startup doesn't fail on unknown keys.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )

    # API keys (optional for local/dev runs). If you plan to use LLM and web-search
    # features in production, set these in your environment or in a .env file.
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    TAVILY_API_KEY: Optional[str] = None
    SERPAPI_API_KEY: Optional[str] = None
    OPENROUTING_API_KEY: Optional[str] = None
    OPENWEATHER_API_KEY: Optional[str] = None
    
    # Financial data APIs
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    FRED_API_KEY: Optional[str] = None
    
    # Optional / deployment settings
    MONGO_URI: Optional[str] = None
    FASTAPI_HOST: str = "0.0.0.0"
    FASTAPI_PORT: int = 8000
    DEBUG: bool = False
    
    # Optional comma-separated list of allowed CORS origins
    ALLOWED_ORIGINS: Optional[str] = None


# Single settings instance for app-wide use
settings = Settings()

__all__ = ["Settings", "settings"]