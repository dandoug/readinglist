"""
Configuration module for the Flask application managing environment-specific settings.

This module handles loading configuration settings from environment variables and provides
different configuration classes for development, production, and testing environments.
It includes settings for:
- Database connections (MySQL/SQLAlchemy)
- Security configurations (passwords, cookies, sessions)
- Email settings
- Logging configurations
- API integrations
"""
import logging
import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

# Calculate the path to where the SQL files are
PROJECT_ROOT = Path(__file__).resolve().parent.parent  # Navigate to the project root
INTEGRATION_DIR = PROJECT_ROOT / "tests" / "integration"

# Determine which environment file to load
env = os.getenv("FLASK_ENV", "development").lower()  # Default to "development"
dotenv_path = INTEGRATION_DIR / ".env.testing" if env in {"testing"} else PROJECT_ROOT / ".env"

# Load the appropriate .env file
load_dotenv(str(dotenv_path))


# pylint: disable=too-few-public-methods
class Config:
    """Base configuration with default settings."""
    SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key")
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = SECRET_KEY
    WTF_CSRF_TIME_LIMIT = 3600  # CSRF token expiration in seconds

    RDS_HOSTNAME = os.getenv("RDS_HOSTNAME")
    RDS_PORT     = os.getenv("RDS_PORT", "3306")
    RDS_DB_NAME  = os.getenv("RDS_DB_NAME", "readinglist")
    RDS_USERNAME = os.getenv("RDS_USERNAME", "readinglist")
    RDS_PASSWORD = os.getenv("RDS_PASSWORD")

    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Avoid overhead of tracking

    # Add any other app-wide default configurations here
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t", "yes")

    #  Flask-Mailman settings
    MAIL_SERVER   = os.getenv("MAIL_SERVER")
    MAIL_PORT     = os.getenv("MAIL_PORT")
    MAIL_USE_TLS  = os.getenv("MAIL_USE_TLS")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

    # Generate a good salt for password hashing using: secrets.SystemRandom().getrandbits(128)
    SECURITY_PASSWORD_SALT = os.environ.get("SECURITY_PASSWORD_SALT")

    # API key for ASIN service
    ASIN_DATA_API_KEY = os.environ.get("ASIN_DATA_API_KEY")
    ASIN_DATA_API_URL = os.environ.get("ASIN_DATA_API_URL", 'https://api.asindataapi.com/request')

    # have session and remember cookie be samesite (flask/flask_login)
    REMEMBER_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True  # Ensures cookies are sent only over HTTPS
    REMEMBER_COOKIE_SECURE = True  # For "remember me" functionality

    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    SECURITY_TOKEN_MAX_AGE = 3600  # 1 hour for security tokens

    SECURITY_USERNAME_ENABLE = False  # keep it simple, just email
    SECURITY_USE_REGISTER_V2 = True
    SECURITY_REGISTERABLE = False  # we provide our own register view
    SECURITY_POST_REGISTER_VIEW = "/admin/user/"

    SECURITY_EMAIL_SENDER = os.getenv("SECURITY_EMAIL_SENDER")

    SECURITY_CONFIRMABLE = True
    SECURITY_RECOVERABLE = True
    SECURITY_PASSWORD_HISTORY = 5
    SECURITY_RESET_PASSWORD_WITHIN = '1 hours'

    FLASK_ADMIN_SWATCH = "sandstone"

    RATELIMIT_ENABLED = True

    # Logging configuration - override in specific environments
    LOGGING_LEVEL = logging.INFO  # Default logging level

    CACHE_TYPE = "SimpleCache"  # This configures an in-memory cache
    CACHE_DEFAULT_TIMEOUT = 300  # Values are cached for 300 seconds (5 minutes) by default

    @classmethod
    def configure_logging(cls):
        """
        Configures logging for the application.

        This method sets up global logging with the specified logging level. Additionally,
        SQLAlchemy-specific logging is configured to the same level.
        """
        # Global logging setup
        logging.basicConfig(level=cls.LOGGING_LEVEL)  # Set the logging level dynamically

        # Configure SQLAlchemy specific logging
        logging.getLogger("sqlalchemy.engine").setLevel(cls.LOGGING_LEVEL)


class DevelopmentConfig(Config):
    """Development-specific configuration."""
    DEBUG = True
    LOGGING_LEVEL = logging.INFO
    SQLALCHEMY_ECHO = False  # Log SQL queries for debugging
    SQLALCHEMY_DATABASE_URI = (f"mysql+pymysql://{Config.RDS_USERNAME}:" +
                               f"{quote_plus(str(Config.RDS_PASSWORD))}@{Config.RDS_HOSTNAME}:" +
                               f"{Config.RDS_PORT}/{Config.RDS_DB_NAME}")
    TEMPLATES_AUTO_RELOAD = True


class ProductionConfig(Config):
    """Production-specific configuration."""
    DEBUG = False
    LOGGING_LEVEL = logging.WARNING
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_DATABASE_URI = (f"mysql+pymysql://{Config.RDS_USERNAME}:" +
                               f"{quote_plus(str(Config.RDS_PASSWORD))}@{Config.RDS_HOSTNAME}:" +
                               f"{Config.RDS_PORT}/{Config.RDS_DB_NAME}")
    cookie_domain = os.getenv("COOKIE_DOMAIN")
    if cookie_domain:
        REMEMBER_COOKIE_DOMAIN = cookie_domain
        SESSION_COOKIE_DOMAIN = cookie_domain


class TestingConfig(Config):
    """Testing-specific configuration."""
    TESTING = True
    DEBUG = True
    LOGGING_LEVEL = logging.WARNING
    RATELIMIT_ENABLED = False  # Disable rate-limiting in testing
    SERVER_NAME = '0.0.0.0:8000'
    SQLALCHEMY_DATABASE_URI = (f"mysql+pymysql://{Config.RDS_USERNAME}:" +
                               f"{quote_plus(str(Config.RDS_PASSWORD))}@{Config.RDS_HOSTNAME}:" +
                               f"{Config.RDS_PORT}/{Config.RDS_DB_NAME}")

    # pylint: disable=invalid-name
    def __init__(self):
        super().__init__()

        # Workaround for running tests in a container locally under act
        # see(https://github.com/nektos/act)
        if os.getenv("ACT") and os.getenv("RDS_HOSTNAME") == "localhost":
            self.RDS_HOSTNAME = "host.docker.internal"
            self.SQLALCHEMY_DATABASE_URI = (f"mysql+pymysql://{Config.RDS_USERNAME}:" +
                                            f"{quote_plus(str(Config.RDS_PASSWORD))}" +
                                            f"@{self.RDS_HOSTNAME}:" +
                                            f"{Config.RDS_PORT}/{Config.RDS_DB_NAME}")
        if os.getenv("ACT") and os.getenv("mail_server") == "localhost":
            self.MAIL_SERVER = "host.docker.internal"


# Automatically configure logging for the chosen environment
def configure_app_logging(environment="development"):
    """
    Configures the application logging based on the given environment.

    This function retrieves a configuration class corresponding to the provided
    environment and applies its logging configuration. It is used to ensure that
    the application's logging adheres to the desired environment-specific
    settings.
    """
    config_class = _config_by_name[environment]
    config_class.configure_logging()


# A dictionary to easily map environment modes to configuration classes
_config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


__all__ = ["Config", "DevelopmentConfig", "ProductionConfig", "TestingConfig",
           "configure_app_logging", "PROJECT_ROOT"]
