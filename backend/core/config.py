import os
from typing import Optional, Type, Union
from dotenv import load_dotenv
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from urllib.parse import quote_plus

from logs import logs_config


load_dotenv()


class BaseConfig:
    """Base configuration with common settings across all environments."""
    
    # Flask core settings
    HOST: str = os.getenv('HOST')
    PORT: int = int(os.getenv('PORT'))
    SECRET_KEY: str = os.getenv('SECRET_KEY')
    API_BASE_URL: str = os.getenv('API_BASE_URL')
    
    # JWT settings
    JWT_SECRET_KEY: str = os.getenv('JWT_SECRET_KEY')
    TOKEN_API_KEY: str = os.getenv('TOKEN_API_KEY')

    # Sentry settings (loaded but not initialized in base)
    SENTRY_DSN: Optional[str] = os.getenv('SENTRY_DSN')
    SENTRY_ENVIRONMENT: str = os.getenv('SENTRY_ENVIRONMENT', 'development')
    SENTRY_TRACES_SAMPLE_RATE: float = float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0.0'))


class DevelopmentConfig(BaseConfig):
    """Development environment configuration."""
    
    DEBUG: bool = True
    TESTING: bool = True
    PROPAGATE_EXCEPTIONS: bool = True


class StagingConfig(BaseConfig):
    """Staging environment configuration."""
    
    DEBUG: bool = False
    TESTING: bool = True
    PROPAGATE_EXCEPTIONS: bool = True


class ProductionConfig(BaseConfig):
    """Production environment configuration."""
    
    DEBUG: bool = False
    TESTING: bool = False
    PROPAGATE_EXCEPTIONS: bool = False


# Environment to config class mapping
_CONFIG_MAP = {
    'development': DevelopmentConfig,
    'staging': StagingConfig,
    'production': ProductionConfig
}


def get_config() -> Union[DevelopmentConfig, StagingConfig, ProductionConfig]:
    """
    Get configuration instance based on ENVIRONMENT variable.
    
    Returns:
        Configuration instance for current environment.
        Defaults to DevelopmentConfig if ENVIRONMENT is not set or invalid.
    """
    environment = os.getenv('ENVIRONMENT', 'development').lower()
    config_class: Type[BaseConfig] = _CONFIG_MAP.get(environment, DevelopmentConfig)
    return config_class()


def init_sentry(config: BaseConfig) -> None:
    """
    Initialize Sentry for error tracking (production only).
    
    Sentry is only initialized when:
    - Environment is 'production'
    - SENTRY_DSN is configured
    
    Args:
        config: Configuration instance containing Sentry settings.
    
    Returns:
        None
    """
    environment = os.getenv('ENVIRONMENT', 'development').lower()
    
    # Only initialize Sentry in production with valid DSN
    if environment != 'production':
        return
    
    if not config.SENTRY_DSN:
        return
    
    try:
        sentry_sdk.init(
            dsn=config.SENTRY_DSN,
            environment=config.SENTRY_ENVIRONMENT,
            traces_sample_rate=config.SENTRY_TRACES_SAMPLE_RATE,
            profiles_sample_rate=config.SENTRY_TRACES_SAMPLE_RATE,  # Match traces rate
            send_default_pii=False,  # Don't send personally identifiable information by default
            attach_stacktrace=True,
            enable_logs=True,
            integrations=[
                FlaskIntegration(
                    transaction_style="url",
                )
            ]
        )
    except Exception as exc:
        # Log error but don't crash the application
        logs_config.logger.warning(f"Failed to initialize Sentry: {exc}")


# Export the active configuration
APP_CONFIG = get_config()