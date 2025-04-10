"""Application configuration module."""

import logging
from typing import Any, Dict, Optional

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
        DATABASE_URL: Database connection string.
        LOG_LEVEL: Logging level.
        QR_CODE_BASE_URL: Base URL for QR code generation.
    """

    # Application settings
    APP_NAME: str = "FastAPI Backend"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "local"
    LOG_LEVEL: str = "INFO"

    # Database settings
    DATABASE_URL: Optional[str] = None

    # QR Code settings
    QR_CODE_BASE_URL: str = "https://nutripeek.pro"

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

    @field_validator("QR_CODE_BASE_URL")
    def validate_qr_code_base_url(cls, v: str) -> str:
        """Validate and normalize the QR code base URL.

        Args:
            v: The QR code base URL.

        Returns:
            The normalized QR code base URL.
        """
        # Remove trailing slashes for consistency
        base_url = v.rstrip("/")

        # Ensure URL uses HTTPS unless it's localhost
        if (
            base_url.startswith("http://")
            and not base_url.startswith("http://localhost")
            and not cls.is_development
        ):
            base_url = base_url.replace("http://", "https://")

        logger.debug(f"Normalized QR_CODE_BASE_URL: {base_url}")
        return base_url

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
# Set default log level to INFO if LOG_LEVEL is empty or invalid
log_level = "INFO"
if settings.LOG_LEVEL:
    log_level = settings.LOG_LEVEL.upper()
    # Validate the log level
    if log_level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        logger.warning(f"Invalid LOG_LEVEL: {log_level}, defaulting to INFO")
        log_level = "INFO"

logger.setLevel(getattr(logging, log_level))
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
logger.info(f"QR code base URL: {settings.QR_CODE_BASE_URL}")
