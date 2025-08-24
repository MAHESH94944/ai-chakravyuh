"""Application settings loaded from environment / .env using pydantic-settings.

This module exposes a single `settings` instance that other modules should import
and reference. Required API keys are validated at startup.
"""

from typing import Optional
import os

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict


    class Settings(BaseSettings):
        # Load variables from the .env file (repo root)
        model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

        # Required API keys
        GEMINI_API_KEY: str
        GROQ_API_KEY: str
        TAVILY_API_KEY: str

        # Optional / deployment settings
        MONGO_URI: Optional[str] = None
        FASTAPI_HOST: str = "0.0.0.0"
        FASTAPI_PORT: int = 8000
        DEBUG: bool = False


    # Single settings instance for app-wide use
    settings = Settings()

except Exception:
    # Lightweight fallback if pydantic-settings isn't installed in the dev env.
    # This keeps the module importable while still allowing local testing.
    from dotenv import load_dotenv

    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))


    class Settings:  # simple container
        GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
        GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
        TAVILY_API_KEY: Optional[str] = os.getenv("TAVILY_API_KEY")
        MONGO_URI: Optional[str] = os.getenv("MONGO_URI")
        FASTAPI_HOST: str = os.getenv("FASTAPI_HOST", "0.0.0.0")
        FASTAPI_PORT: int = int(os.getenv("FASTAPI_PORT", "8000"))
        DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("1", "true", "yes")


    settings = Settings()

__all__ = ["Settings", "settings"]