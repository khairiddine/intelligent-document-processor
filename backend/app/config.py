"""
Application Configuration
"""
from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "Document Processing API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str
    
    # Security
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "https://e43298d7-bcf2-4c6f-8ee1-e4e6a96b1cf7.lovableproject.com",
        "https://*.lovableproject.com",  # Allow all Lovable previews
        # Add your Render URL after deployment:
        # "https://document-processing-api.onrender.com"
    ]
    
    # File Upload
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".png", ".jpg", ".jpeg"]
    
    # Azure (from your existing config)
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_ENDPOINT: str
    AZURE_API_VERSION: str = "2024-12-01-preview"
    AZURE_DI_ENDPOINT: str
    AZURE_DI_KEY: str
    MODEL: str = "azure/gpt-4o"
    
    # Phoenix
    PHOENIX_API_KEY: str = ""
    PHOENIX_COLLECTOR_ENDPOINT: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Load settings
settings = Settings()
