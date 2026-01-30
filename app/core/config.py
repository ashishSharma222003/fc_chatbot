"""
Application Configuration

This file manages application settings using Pydantic Settings.
It reads environment variables from the .env file and provides a centralized
place to access configuration values like database URLs, API keys, and project metadata.
"""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "FC Chatbot"
    API_V1_STR: str = "/api/v1"
    
    # Add other settings here (DB, Auth, etc.)

    class Config:
        env_file = ".env"

settings = Settings()
