"""Database package for Loan Dashboard."""

from database.db_manager import (
    DatabaseManager,
    get_db,
    get_db_manager,
    init_app,
    close_db
)

__all__ = [
    'DatabaseManager',
    'get_db',
    'get_db_manager',
    'init_app',
    'close_db'
]
