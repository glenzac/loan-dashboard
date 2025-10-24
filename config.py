"""
Configuration settings for Flask application.

This module contains configuration classes for different environments
(development, testing, production).
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.absolute()

class Config:
    """Base configuration class."""

    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24)

    # Session settings
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_FILE_DIR = os.path.join(BASE_DIR, 'flask_session')
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_HTTPONLY = True

    # Database settings
    DATABASE_PATH = os.path.join(BASE_DIR, 'loan_dashboard.db')
    BACKUP_DIR = os.path.join(BASE_DIR, 'backups')

    # Upload settings (for future file uploads)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

    # Application settings
    ITEMS_PER_PAGE = 20
    MAX_FORECAST_SCENARIOS = 5


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False


class TestingConfig(Config):
    """Testing configuration."""

    DEBUG = False
    TESTING = True
    DATABASE_PATH = ':memory:'  # Use in-memory database for tests
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True  # Require HTTPS

    # Use environment variable for secret key in production
    SECRET_KEY = os.environ.get('SECRET_KEY')

    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set in production")


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
