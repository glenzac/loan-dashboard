"""
Database Manager module for handling all SQLite operations.
Adapted for Flask with request-scoped connections.
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Tuple

# Flask-specific imports (will be available when used in Flask context)
try:
    from flask import g, current_app
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False


class DatabaseManager:
    """Handles all database operations for the loan dashboard."""

    def __init__(self, db_path: str = None):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file (defaults to config value in Flask)
        """
        if db_path is None:
            # Try to get from Flask config, otherwise use default
            if FLASK_AVAILABLE:
                try:
                    db_path = current_app.config.get('DATABASE_PATH', 'loan_dashboard.db')
                except RuntimeError:
                    # Not in Flask application context
                    db_path = 'loan_dashboard.db'
            else:
                db_path = 'loan_dashboard.db'

        self.db_path = db_path
        self.connection = None

    def connect(self):
        """Establish database connection."""
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row  # Enable column access by name

            # Enable foreign key constraints (required for CASCADE DELETE)
            self.connection.execute("PRAGMA foreign_keys = ON")

            return self.connection
        except sqlite3.Error as e:
            raise Exception(f"Failed to connect to database: {e}")

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def create_tables(self):
        """Create all tables from schema.sql if they don't exist."""
        try:
            schema_path = Path(__file__).parent / 'schema.sql'

            with open(schema_path, 'r') as f:
                schema_sql = f.read()

            if not self.connection:
                self.connect()

            cursor = self.connection.cursor()
            cursor.executescript(schema_sql)
            self.connection.commit()

            return True
        except sqlite3.Error as e:
            raise Exception(f"Failed to create tables: {e}")
        except FileNotFoundError:
            raise Exception(f"Schema file not found at {schema_path}")

    def execute_query(self, query: str, params: Optional[Tuple] = None) -> int:
        """
        Execute a SQL query (INSERT, UPDATE, DELETE).

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            lastrowid for INSERT operations, rowcount for UPDATE/DELETE
        """
        try:
            if not self.connection:
                self.connect()

            cursor = self.connection.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            self.connection.commit()

            # Auto-export to CSV after write operations (optional)
            query_upper = query.strip().upper()
            if query_upper.startswith(('INSERT', 'UPDATE', 'DELETE')):
                self._trigger_csv_export()

            # Return lastrowid for INSERT, rowcount for UPDATE/DELETE
            return cursor.lastrowid if cursor.lastrowid else cursor.rowcount

        except sqlite3.Error as e:
            self.connection.rollback()
            raise Exception(f"Query execution failed: {e}")

    def _trigger_csv_export(self):
        """Trigger CSV export after database write operations."""
        try:
            from utils.csv_sync import get_csv_sync
            csv_sync = get_csv_sync()
            csv_sync.export_all_tables()
        except Exception as e:
            # Log error but don't fail the transaction
            pass  # Silently ignore CSV export errors

    def fetch_all(self, query: str, params: Optional[Tuple] = None) -> List[sqlite3.Row]:
        """
        Fetch all results from a SELECT query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            List of Row objects
        """
        try:
            if not self.connection:
                self.connect()

            cursor = self.connection.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            return cursor.fetchall()

        except sqlite3.Error as e:
            raise Exception(f"Query fetch failed: {e}")

    def fetch_one(self, query: str, params: Optional[Tuple] = None) -> Optional[sqlite3.Row]:
        """
        Fetch single result from a SELECT query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Single Row object or None
        """
        try:
            if not self.connection:
                self.connect()

            cursor = self.connection.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            return cursor.fetchone()

        except sqlite3.Error as e:
            raise Exception(f"Query fetch failed: {e}")

    def backup_database(self) -> str:
        """
        Create a timestamped backup of the database.

        Returns:
            Path to backup file
        """
        try:
            # Get backup directory from config or use default
            if FLASK_AVAILABLE:
                try:
                    backup_dir = current_app.config.get('BACKUP_DIR', 'backups')
                except RuntimeError:
                    backup_dir = 'backups'
            else:
                backup_dir = 'backups'

            # Create backup directory if it doesn't exist
            backup_path = Path(backup_dir)
            backup_path.mkdir(exist_ok=True)

            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = backup_path / f'loan_dashboard_backup_{timestamp}.db'

            # Create backup using SQLite backup API
            if not self.connection:
                self.connect()

            backup_conn = sqlite3.connect(str(backup_file))

            with backup_conn:
                self.connection.backup(backup_conn)

            backup_conn.close()

            return str(backup_file)

        except Exception as e:
            raise Exception(f"Backup failed: {e}")

    def get_table_count(self, table_name: str) -> int:
        """
        Get row count for a specific table.

        Args:
            table_name: Name of the table (must be in whitelist)

        Returns:
            Number of rows

        Raises:
            ValueError: If table_name is not in the whitelist of valid tables
        """
        # Whitelist of valid table names to prevent SQL injection
        VALID_TABLES = {
            'loans',
            'payments',
            'interest_rate_history',
            'loan_disbursements',
            'forecast_scenarios'
        }

        if table_name not in VALID_TABLES:
            raise ValueError(f"Invalid table name: '{table_name}'. Must be one of: {', '.join(sorted(VALID_TABLES))}")

        # Safe to use f-string now since table_name is validated against whitelist
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        result = self.fetch_one(query)
        return result['count'] if result else 0

    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database.

        Args:
            table_name: Name of the table

        Returns:
            True if table exists, False otherwise
        """
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        result = self.fetch_one(query, (table_name,))
        return result is not None


# ============================================================================
# Flask-specific functions
# ============================================================================

def get_db():
    """
    Get database connection for current Flask request context.
    Stores connection in Flask's g object for request lifetime.

    Returns:
        DatabaseManager instance
    """
    if not FLASK_AVAILABLE:
        raise RuntimeError("Flask is not available. Use get_db_manager() instead.")

    if 'db' not in g:
        g.db = DatabaseManager()
        g.db.connect()
    return g.db


def close_db(e=None):
    """
    Close database connection at end of Flask request.

    Args:
        e: Exception if any occurred during request
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_app(app):
    """
    Initialize database with Flask app.

    Args:
        app: Flask application instance
    """
    # Register teardown function to close DB connections
    app.teardown_appcontext(close_db)

    # Create tables on first run
    with app.app_context():
        db = DatabaseManager()
        db.connect()
        db.create_tables()
        db.close()
        print("✅ Database initialized and tables created")


# ============================================================================
# Standalone function (backwards compatibility)
# ============================================================================

# Singleton instance for application-wide use (non-Flask contexts)
_db_instance = None


def get_db_manager() -> DatabaseManager:
    """
    Get or create singleton DatabaseManager instance.

    This is for non-Flask contexts or when you need a standalone instance.
    For Flask request contexts, use get_db() instead.

    Returns:
        DatabaseManager instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
        _db_instance.connect()
        _db_instance.create_tables()
    return _db_instance
