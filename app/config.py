import os
from urllib.parse import quote_plus

from dotenv import load_dotenv

# Load environment variables from a .env file, if it exists
load_dotenv()


class Config:
    """Base configuration with default settings."""
    SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key")  # Replace with an env-defined secret

    RDS_HOSTNAME = os.getenv("RDS_HOSTNAME")
    RDS_PORT = os.getenv("RDS_PORT", "3306")
    RDS_DB_NAME = os.getenv("RDS_DB_NAME", "readinglist")
    RDS_USERNAME = os.getenv("RDS_USERNAME", "readinglist")
    RDS_PASSWORD = os.getenv("RDS_PASSWORD")

    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{RDS_USERNAME}:{quote_plus(str(RDS_PASSWORD))}@{RDS_HOSTNAME}:{RDS_PORT}/{RDS_DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Avoid overhead of tracking

    # Add any other app-wide default configurations here
    DEBUG = os.getenv("DEBUG", False)


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