"""Application configuration module."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Configure logger
logger = logging.getLogger("app.config")

# Determine env file path
DEFAULT_ENV_FILE = ".env"
LOCAL_ENV_FILE = "local.env"  # Updated to match the actual file name


class Settings(BaseSettings):
    """Application settings.

    Attributes:
        APP_NAME: Name of the application.
        APP_VERSION: Version of the application.
        DEBUG: Debug mode flag.
        ENVIRONMENT: Environment name (development, staging, production).
        SECRET_KEY: Secret key for security.
        ACCESS_TOKEN_EXPIRE_MINUTES: Token expiration time in minutes.
        DATABASE_URL: Database connection string.
        ALLOWED_HOSTS: List of allowed hosts.
        OPENWEATHERMAP_API_KEY: API key for OpenWeatherMap service.
        GOOGLE_MAPS_API_KEY: API key for Google Maps service.
        LOG_LEVEL: Logging level.
    """

    # Application settings
    APP_NAME: str = "FastAPI Backend"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "local"
    LOG_LEVEL: str = "INFO"

    # Security settings
    SECRET_KEY: str = "your-secret-key-for-development-only"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database settings
    DATABASE_URL: Optional[str] = None

    # CORS settings
    ALLOWED_HOSTS: List[str] = ["*"]

    # Set model_config to use the appropriate env file
    model_config = SettingsConfigDict(
        case_sensitive=True,
        extra="ignore",
        env_file=DEFAULT_ENV_FILE,
    )

    @field_validator("DATABASE_URL")
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        """Validate and process the database URL.

        Args:
            v: The database URL.
            values: Other field values.

        Returns:
            The processed database URL.
        """
        if isinstance(v, str):
            # Log the raw DATABASE_URL for debugging
            logger.debug(f"Raw DATABASE_URL from env: {v}")
            return v
        return None

    @property
    def is_development(self) -> bool:
        """Check if the application is running in development mode.

        Returns:
            True if in development mode, False otherwise.
        """
        return self.ENVIRONMENT.lower() in ("dev", "development", "local")

    @property
    def is_production(self) -> bool:
        """Check if the application is running in production mode.

        Returns:
            True if in production mode, False otherwise.
        """
        return self.ENVIRONMENT.lower() in ("prod", "production")


# Create settings instance
settings = Settings()

# Log settings information - useful for debugging
logger.setLevel(getattr(logging, settings.LOG_LEVEL))
logger.info(f"Loaded settings for environment: {settings.ENVIRONMENT}")
# Mask sensitive parts of the database URL
if settings.DATABASE_URL:
    db_url_parts = str(settings.DATABASE_URL).split("@")
    if len(db_url_parts) > 1:
        masked_url = f"****@{db_url_parts[1]}"
        logger.info(f"Database URL: {masked_url}")
    else:
        logger.info("Database URL is not in the expected format")
else:
    logger.info("Database URL is not configured")
logger.info(f"Debug mode: {settings.DEBUG}")
