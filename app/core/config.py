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
    OPENAI_API_KEY: str
    PINECONE_API_KEY: str
    PINECONE_INDEX_NAME: str
    DATABASE_URL: str = "sqlite:///./sql_app.db"

    class Config:
        env_file = ".env"

settings = Settings()
