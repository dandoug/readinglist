import os
from urllib.parse import quote_plus

from dotenv import load_dotenv

# Load environment variables from a .env file, if it exists
load_dotenv()


class Config:
    """Base configuration with default settings."""
    SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key")

    RDS_HOSTNAME = os.getenv("RDS_HOSTNAME")
    RDS_PORT     = os.getenv("RDS_PORT", "3306")
    RDS_DB_NAME  = os.getenv("RDS_DB_NAME", "readinglist")
    RDS_USERNAME = os.getenv("RDS_USERNAME", "readinglist")
    RDS_PASSWORD = os.getenv("RDS_PASSWORD")

    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{RDS_USERNAME}:{quote_plus(str(RDS_PASSWORD))}@{RDS_HOSTNAME}:{RDS_PORT}/{RDS_DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Avoid overhead of tracking

    # Add any other app-wide default configurations here
    DEBUG = os.getenv("DEBUG", False)

    #  Flask-Mailman settings
    MAIL_SERVER   = os.getenv("MAIL_SERVER")
    MAIL_PORT     = os.getenv("MAIL_PORT")
    MAIL_USE_TLS  = os.getenv("MAIL_USE_TLS")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

    # Generate a good salt for password hashing using: secrets.SystemRandom().getrandbits(128), put in env
    SECURITY_PASSWORD_SALT = os.environ.get("SECURITY_PASSWORD_SALT")

    # API key for ASIN service
    ASIN_DATA_API_KEY = os.environ.get("ASIN_DATA_API_KEY")

    # have session and remember cookie be samesite (flask/flask_login)
    REMEMBER_COOKIE_SAMESITE = "strict"
    SESSION_COOKIE_SAMESITE = "strict"

    SECURITY_USERNAME_ENABLE = False  # keep it simple, just email
    SECURITY_USE_REGISTER_V2 = True
    SECURITY_REGISTERABLE=False  # we provide our own register view to only allow admin role to register
    SECURITY_POST_REGISTER_VIEW = "/admin/user/"

    SECURITY_EMAIL_SENDER = os.getenv("SECURITY_EMAIL_SENDER")

    SECURITY_CONFIRMABLE = True
    SECURITY_RECOVERABLE = True

    FLASK_ADMIN_SWATCH = "sandstone"


class DevelopmentConfig(Config):
    """Development-specific configuration."""
    DEBUG = True
    SQLALCHEMY_ECHO = True  # Log SQL queries for debugging


class ProductionConfig(Config):
    """Production-specific configuration."""
    DEBUG = False
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    """Testing-specific configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"  # Use an in-memory database for testing


# A dictionary to easily map environment modes to configuration classes
config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
