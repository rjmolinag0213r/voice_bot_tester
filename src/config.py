"""Configuration management for voice bot testing system."""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Twilio Configuration
    twilio_account_sid: str = Field(..., alias="TWILIO_ACCOUNT_SID")
    twilio_auth_token: str = Field(..., alias="TWILIO_AUTH_TOKEN")
    twilio_phone_number: str = Field(..., alias="TWILIO_PHONE_NUMBER")
    
    # OpenRouter Configuration
    openrouter_api_key: str = Field(..., alias="OPENROUTER_API_KEY")
    
    # Target Configuration
    target_phone_number: str = Field(default="+18054398008", alias="TARGET_PHONE_NUMBER")
    
    # LLM Configuration
    llm_model: str = Field(default="anthropic/claude-3.5-sonnet", alias="LLM_MODEL")
    llm_temperature: float = Field(default=0.8, alias="LLM_TEMPERATURE")
    
    # Call Configuration
    min_call_duration: int = Field(default=60, alias="MIN_CALL_DURATION")
    max_call_duration: int = Field(default=180, alias="MAX_CALL_DURATION")
    total_calls: int = Field(default=12, alias="TOTAL_CALLS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def get_settings() -> Settings:
    """Get application settings."""
    from dotenv import load_dotenv
    load_dotenv()
    return Settings()
