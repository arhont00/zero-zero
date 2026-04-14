"""
Secure configuration with environment validation and secrets management.
Production-ready with no hardcoded secrets.
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseSettings, Field, validator
from typing import Optional

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / '.env'
load_dotenv(ENV_FILE)


class SecretStr(str):
    """String that won't be logged"""
    def __repr__(self):
        return "<SecretStr: ***>"


class Settings(BaseSettings):
    """Application settings with validation."""
    
    # === BOT CONFIGURATION ===
    BOT_TOKEN: str = Field(..., env='BOT_TOKEN')
    ADMIN_ID: int = Field(default=0, env='ADMIN_ID')
    CHANNEL_ID: Optional[str] = Field(default=None, env='CHANNEL_ID')
    
    # === DATABASE ===
    DB_PATH: Path = Field(default=BASE_DIR / 'data' / 'bot.db', env='DB')
    DATA_DIR: Path = Field(default=BASE_DIR / 'data')
    
    # === REDIS ===
    REDIS_URL: str = Field(default='redis://localhost:6379/0', env='REDIS_URL')
    REDIS_PASSWORD: Optional[SecretStr] = Field(default=None, env='REDIS_PASSWORD')
    
    # === STORAGE ===
    STORAGE_PATH: Path = Field(default=None)
    DIAGNOSTICS_PATH: Path = Field(default=None)
    STORIES_PATH: Path = Field(default=None)
    PHOTOS_PATH: Path = Field(default=None)
    
    # === CONTENT ===
    CONTENT_PATH: Path = Field(default=None)
    KNOWLEDGE_BASE_PATH: Path = Field(default=BASE_DIR / 'content' / 'knowledge_base')
    POSTS_PATH: Path = Field(default=None)
    CLUB_CONTENT_PATH: Path = Field(default=None)  
    
    # === INTEGRATIONS ===
    AMOCRM_SUBDOMAIN: Optional[str] = Field(default=None, env='AMOCRM_SUBDOMAIN')
    AMOCRM_ACCESS_TOKEN: Optional[SecretStr] = Field(default=None, env='AMOCRM_ACCESS_TOKEN')
    GEMINI_API_KEY: Optional[SecretStr] = Field(default=None, env='GEMINI_API_KEY')
    
    # === LIMITS ===
    AI_DAILY_LIMIT: int = Field(default=3, env='AI_DAILY_LIMIT')
    
    # === SECURITY ===
    CORS_ORIGINS: list = Field(default=['https://example.com'], env='CORS_ORIGINS')
    RATE_LIMIT_REQUESTS: int = Field(default=100, env='RATE_LIMIT_REQUESTS')
    RATE_LIMIT_WINDOW: int = Field(default=60, env='RATE_LIMIT_WINDOW')
    
    # === WEB ===
    ENABLE_WEB: bool = Field(default=True, env='ENABLE_WEB')
    WEB_PORT: int = Field(default=8080, env='PORT')
    DEBUG: bool = Field(default=False, env='DEBUG')
    
    # === LOGGING ===
    LOG_LEVEL: str = Field(default='INFO', env='LOG_LEVEL')
    SENTRY_DSN: Optional[str] = Field(default=None, env='SENTRY_DSN')
    
    class Config:
        env_file = str(ENV_FILE)
        case_sensitive = True
    
    @validator('BOT_TOKEN', pre=True)
    def validate_bot_token(cls, v):
        """Validate BOT_TOKEN is set."""
        if not v or not isinstance(v, str) or len(v) < 10:
            raise ValueError("Invalid BOT_TOKEN format")
        return v
    
    @validator('ADMIN_ID', pre=True)
    def validate_admin_id(cls, v):
        """Validate ADMIN_ID."""
        try:
            if not v or v == '0':
                return 0
            return int(v)
        except (ValueError, TypeError):
            return 0
    
    def __init__(self, **data):
        super().__init__(**data)
        # Create required directories
        self._create_directories()
    
    def _create_directories(self):
        """Create all required directories."""
        self.STORAGE_PATH = self.DATA_DIR / 'storage'
        self.DIAGNOSTICS_PATH = self.STORAGE_PATH / 'diagnostics'
        self.STORIES_PATH = self.STORAGE_PATH / 'stories'
        self.PHOTOS_PATH = self.STORAGE_PATH / 'photos'
        self.CONTENT_PATH = self.DATA_DIR / 'content'
        dirs_to_create = [
            self.DB_PATH.parent,
            self.DATA_DIR,
            self.STORAGE_PATH,
            self.DIAGNOSTICS_PATH,
            self.STORIES_PATH,
            self.PHOTOS_PATH,
            self.CONTENT_PATH,
            self.POSTS_PATH = self.CONTENT_PATH / 'posts',
            self.CLUB_CONTENT_PATH = self.CONTENT_PATH / 'club',
        ]
        
        for dir_path in dirs_to_create:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error(f"Failed to create directory {dir_path}: {e}")
                raise
    
    def validate_all(self) -> bool:
        """Validate all required configuration."""
        if not self.BOT_TOKEN:
            raise ValueError("❌ BOT_TOKEN not set in environment variables")
        
        logger.info("✅ Configuration validated successfully")
        return True
    
    def get_summary(self) -> str:
        """Get configuration summary (safe to log)."""
        return f"""
Configuration Summary:
  BOT_TOKEN: {'✅ Set' if self.BOT_TOKEN else '❌ Missing'}
  ADMIN_ID: {self.ADMIN_ID}
  DB_PATH: {self.DB_PATH}
  REDIS_URL: {'✅ Configured' if self.REDIS_URL else '❌ Missing'}
  CORS_ORIGINS: {len(self.CORS_ORIGINS)} origins configured
  DEBUG: {self.DEBUG}
"""


# Global config instance
Config = Settings()