"""
CSV Export/Restore Utility for Git Tracking and Database Recovery
"""

import os
import csv
import sqlite3
from datetime import datetime
from typing import Dict, List, Tuple
import shutil


class CSVSync:
    """Handle CSV export and restore for database backup and version control."""

    def __init__(self, db_path: str = "loan_dashboard.db", csv_dir: str = "data"):
        self.db_path = db_path
        self.csv_dir = csv_dir
        self.ensure_csv_directory()

        # Define tables and their columns in dependency order
        self.tables = {
            'loans': [
                'loan_id', 'loan_name', 'loan_type', 'bank_name',
                'principal_amount', 'sanctioned_amount', 'interest_rate',
                'rate_type', 'loan_term_months', 'start_date', 'emi_amount',
                'payment_frequency', 'status', 'created_at', 'updated_at'
            ],
            'payments': [
                'payment_id', 'loan_id', 'payment_date', 'scheduled_date',
                'principal_component', 'interest_component', 'total_amount',
                'payment_type', 'payment_method', 'charges', 'balance_remaining',
                'status', 'notes', 'created_at'
            ],
            'interest_rate_history': [
                'rate_id', 'loan_id', 'effective_date', 'interest_rate',
                'reason', 'created_at'
            ],
            'loan_disbursements': [
                'disbursement_id', 'loan_id', 'disbursement_date',
                'amount', 'new_emi', 'created_at'
            ],
            'forecast_scenarios': [
                'scenario_id', 'loan_id', 'scenario_name', 'prepayment_type',
                'prepayment_value', 'start_month', 'created_at'
            ]
        }

    def ensure_csv_directory(self):
        """Ensure CSV directory exists."""
        os.makedirs(self.csv_dir, exist_ok=True)

    def get_csv_path(self, table_name: str) -> str:
        """Get CSV file path for a table."""
        return os.path.join(self.csv_dir, f"{table_name}.csv")

    def export_table_to_csv(self, table_name: str) -> Tuple[bool, str]:
        """
        Export a single table to CSV.

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if not os.path.exists(self.db_path):
                return False, f"Database not found: {self.db_path}"

            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get data
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()

            csv_path = self.get_csv_path(table_name)

            # Write to CSV
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                if rows:
                    # Get column names from first row
                    columns = rows[0].keys()
                    writer = csv.DictWriter(f, fieldnames=columns)
                    writer.writeheader()

                    for row in rows:
                        writer.writerow(dict(row))
                else:
                    # Empty table - write header only
                    columns = self.tables.get(table_name, [])
                    if columns:
                        writer = csv.DictWriter(f, fieldnames=columns)
                        writer.writeheader()

            conn.close()
            return True, f"Exported {len(rows)} rows from {table_name}"

        except Exception as e:
            return False, f"Error exporting {table_name}: {str(e)}"

    def export_all_tables(self) -> Dict[str, Tuple[bool, str]]:
        """
        Export all tables to CSV.

        Returns:
            Dictionary of table_name -> (success, message)
        """
        results = {}

        for table_name in self.tables.keys():
            success, message = self.export_table_to_csv(table_name)
            results[table_name] = (success, message)

        # Write sync metadata
        self.write_sync_metadata()

        return results

    def write_sync_metadata(self):
        """Write metadata about last sync."""
        metadata_path = os.path.join(self.csv_dir, 'last_sync.txt')
        with open(metadata_path, 'w') as f:
            f.write(f"Last sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Database: {self.db_path}\n")

    def restore_table_from_csv(self, table_name: str, conn: sqlite3.Connection) -> Tuple[bool, str]:
        """
        Restore a single table from CSV.

        Args:
            table_name: Name of table to restore
            conn: Active database connection

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            csv_path = self.get_csv_path(table_name)

            if not os.path.exists(csv_path):
                return False, f"CSV not found: {csv_path}"

            cursor = conn.cursor()

            # Read CSV
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            if not rows:
                return True, f"No data to restore for {table_name}"

            # Get columns from CSV
            columns = list(rows[0].keys())

            # Build INSERT query with explicit column names
            placeholders = ', '.join(['?' for _ in columns])
            columns_str = ', '.join(columns)

            insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"

            # Insert data
            for row in rows:
                values = [row.get(col) for col in columns]
                # Convert empty strings to None for numeric fields
                values = [None if v == '' else v for v in values]
                cursor.execute(insert_query, values)

            conn.commit()
            return True, f"Restored {len(rows)} rows to {table_name}"

        except Exception as e:
            conn.rollback()
            return False, f"Error restoring {table_name}: {str(e)}"

    def restore_from_csv(self) -> Dict[str, Tuple[bool, str]]:
        """
        Restore entire database from CSV files.

        Returns:
            Dictionary of table_name -> (success, message)
        """
        results = {}

        try:
            # Backup existing database if it exists
            if os.path.exists(self.db_path):
                backup_path = f"{self.db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(self.db_path, backup_path)
                results['_backup'] = (True, f"Backed up to {backup_path}")

                # Delete existing database
                os.remove(self.db_path)

            # Create new database with schema
            conn = sqlite3.connect(self.db_path)

            # Read and execute schema
            schema_path = 'database/schema.sql'
            if os.path.exists(schema_path):
                with open(schema_path, 'r') as f:
                    schema_sql = f.read()
                    conn.executescript(schema_sql)
                results['_schema'] = (True, "Schema created")
            else:
                conn.close()
                return {'_error': (False, "schema.sql not found")}

            # Restore tables in dependency order (loans first, then others)
            for table_name in self.tables.keys():
                success, message = self.restore_table_from_csv(table_name, conn)
                results[table_name] = (success, message)

            # Update autoincrement counters based on max IDs
            cursor = conn.cursor()
            for table_name in self.tables.keys():
                # Get primary key column name
                pk_map = {
                    'loans': 'loan_id',
                    'payments': 'payment_id',
                    'interest_rate_history': 'rate_id',
                    'loan_disbursements': 'disbursement_id',
                    'forecast_scenarios': 'scenario_id'
                }
                pk_col = pk_map.get(table_name)

                if pk_col:
                    # Get max ID
                    cursor.execute(f"SELECT MAX({pk_col}) as max_id FROM {table_name}")
                    result = cursor.fetchone()
                    max_id = result[0] if result[0] else 999

                    # Update sqlite_sequence
                    cursor.execute(
                        "INSERT OR REPLACE INTO sqlite_sequence (name, seq) VALUES (?, ?)",
                        (table_name, max_id)
                    )

            conn.commit()
            conn.close()

            results['_autoincrement'] = (True, "Updated autoincrement counters")

            return results

        except Exception as e:
            return {'_error': (False, f"Restore failed: {str(e)}")}

    def verify_integrity(self) -> Dict[str, any]:
        """
        Verify database integrity by comparing row counts.

        Returns:
            Dictionary with verification results
        """
        try:
            if not os.path.exists(self.db_path):
                return {'error': 'Database not found'}

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            results = {}

            for table_name in self.tables.keys():
                # Count DB rows
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                db_count = cursor.fetchone()[0]

                # Count CSV rows
                csv_path = self.get_csv_path(table_name)
                csv_count = 0
                if os.path.exists(csv_path):
                    with open(csv_path, 'r', encoding='utf-8') as f:
                        csv_count = sum(1 for _ in csv.DictReader(f))

                results[table_name] = {
                    'db_rows': db_count,
                    'csv_rows': csv_count,
                    'match': db_count == csv_count
                }

            conn.close()

            return results

        except Exception as e:
            return {'error': str(e)}


# Global instance
_csv_sync = None

def get_csv_sync() -> CSVSync:
    """Get global CSVSync instance."""
    global _csv_sync
    if _csv_sync is None:
        _csv_sync = CSVSync()
    return _csv_sync
