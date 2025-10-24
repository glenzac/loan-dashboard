"""
Pytest configuration and fixtures for testing.
"""
import pytest
import os
import tempfile
from app import create_app
from database import get_db, DatabaseManager


@pytest.fixture
def app():
    """Create and configure a test Flask application."""
    # Create a temporary file for the test database
    db_fd, db_path = tempfile.mkstemp(suffix='.db')

    # Create app with test config
    app = create_app({
        'TESTING': True,
        'DATABASE_PATH': db_path,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
        'SESSION_TYPE': 'filesystem',
    })

    yield app

    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def db(app):
    """Get database instance for testing."""
    with app.app_context():
        db = get_db()
        yield db
