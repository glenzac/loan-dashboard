"""
Test Database Integration

Tests for verifying database operations work correctly in Flask context.
"""
import pytest
from database.models import Loan, Payment, InterestRateHistory, LoanDisbursement, ForecastScenario
from database import get_db


class TestDatabaseConnection:
    """Test database connection and initialization."""

    def test_database_connection(self, app, db):
        """Test that database connection is established."""
        assert db is not None
        assert db.connection is not None

    def test_tables_created(self, app, db):
        """Test that all required tables are created."""
        required_tables = [
            'loans',
            'payments',
            'interest_rate_history',
            'loan_disbursements',
            'forecast_scenarios'
        ]

        for table in required_tables:
            assert db.table_exists(table), f"Table {table} should exist"

    def test_foreign_keys_enabled(self, app, db):
        """Test that foreign key constraints are enabled."""
        result = db.fetch_one("PRAGMA foreign_keys")
        assert result[0] == 1, "Foreign keys should be enabled"


class TestLoanCRUD:
    """Test Loan model CRUD operations."""

    @pytest.fixture
    def sample_loan_data(self):
        """Sample loan data for testing."""
        return {
            'loan_name': 'Test Home Loan',
            'loan_type': 'HOME',
            'bank_name': 'HDFC Bank',
            'principal_amount': 2000000,
            'sanctioned_amount': 2000000,
            'interest_rate': 8.5,
            'rate_type': 'FIXED',
            'loan_term_months': 240,
            'start_date': '2024-01-01',
            'emi_amount': 17350,
            'payment_frequency': 'MONTHLY',
            'status': 'ACTIVE'
        }

    def test_create_loan(self, app, sample_loan_data):
        """Test creating a new loan."""
        with app.app_context():
            loan_id = Loan.create(sample_loan_data)
            assert loan_id is not None
            assert loan_id > 0

    def test_get_loan_by_id(self, app, sample_loan_data):
        """Test retrieving a loan by ID."""
        with app.app_context():
            # Create loan
            loan_id = Loan.create(sample_loan_data)

            # Retrieve loan
            loan = Loan.get_by_id(loan_id)

            assert loan is not None
            assert loan.loan_name == sample_loan_data['loan_name']
            assert loan.loan_type == sample_loan_data['loan_type']
            assert float(loan.principal_amount) == sample_loan_data['principal_amount']
            assert float(loan.interest_rate) == sample_loan_data['interest_rate']

    def test_get_all_loans(self, app, sample_loan_data):
        """Test retrieving all loans."""
        with app.app_context():
            # Create multiple loans
            loan_id1 = Loan.create(sample_loan_data)

            sample_loan_data['loan_name'] = 'Test Personal Loan'
            sample_loan_data['loan_type'] = 'PERSONAL'
            loan_id2 = Loan.create(sample_loan_data)

            # Retrieve all loans
            loans = Loan.get_all()

            assert len(loans) == 2
            assert loans[0].loan_id in [loan_id1, loan_id2]

    def test_update_loan(self, app, sample_loan_data):
        """Test updating a loan."""
        with app.app_context():
            # Create loan
            loan_id = Loan.create(sample_loan_data)

            # Update loan
            sample_loan_data['loan_name'] = 'Updated Loan Name'
            sample_loan_data['interest_rate'] = 9.0
            Loan.update(loan_id, sample_loan_data)

            # Verify update
            loan = Loan.get_by_id(loan_id)
            assert loan.loan_name == 'Updated Loan Name'
            assert float(loan.interest_rate) == 9.0

    def test_delete_loan(self, app, sample_loan_data):
        """Test deleting a loan."""
        with app.app_context():
            # Create loan
            loan_id = Loan.create(sample_loan_data)

            # Delete loan
            Loan.delete(loan_id)

            # Verify deletion
            loan = Loan.get_by_id(loan_id)
            assert loan is None

    def test_filter_loans_by_status(self, app, sample_loan_data):
        """Test filtering loans by status."""
        with app.app_context():
            # Create active loan
            Loan.create(sample_loan_data)

            # Create closed loan
            sample_loan_data['loan_name'] = 'Closed Loan'
            sample_loan_data['status'] = 'CLOSED'
            Loan.create(sample_loan_data)

            # Get active loans
            active_loans = Loan.get_all(status='ACTIVE')
            assert len(active_loans) == 1
            assert active_loans[0].status == 'ACTIVE'

            # Get closed loans
            closed_loans = Loan.get_all(status='CLOSED')
            assert len(closed_loans) == 1
            assert closed_loans[0].status == 'CLOSED'


class TestPaymentCRUD:
    """Test Payment model CRUD operations."""

    @pytest.fixture
    def loan_with_payments(self, app):
        """Create a loan and return its ID for payment tests."""
        loan_data = {
            'loan_name': 'Test Loan for Payments',
            'loan_type': 'HOME',
            'bank_name': 'Test Bank',
            'principal_amount': 1000000,
            'sanctioned_amount': 1000000,
            'interest_rate': 8.5,
            'rate_type': 'FIXED',
            'loan_term_months': 240,
            'start_date': '2024-01-01',
            'emi_amount': 8678,
            'payment_frequency': 'MONTHLY',
            'status': 'ACTIVE'
        }

        with app.app_context():
            loan_id = Loan.create(loan_data)
            return loan_id

    def test_create_payment(self, app, loan_with_payments):
        """Test creating a payment."""
        with app.app_context():
            payment_data = {
                'loan_id': loan_with_payments,
                'payment_date': '2024-01-05',
                'scheduled_date': '2024-01-05',
                'principal_component': 1511.67,
                'interest_component': 7166.67,
                'total_amount': 8678.34,
                'payment_type': 'EMI',
                'payment_method': 'Auto Debit',
                'charges': 0,
                'balance_remaining': 998488.33,
                'status': 'PAID',
                'notes': 'Test payment'
            }

            payment_id = Payment.create(payment_data)
            assert payment_id is not None
            assert payment_id > 0

    def test_get_payments_by_loan(self, app, loan_with_payments):
        """Test retrieving payments for a loan."""
        with app.app_context():
            # Create payment
            payment_data = {
                'loan_id': loan_with_payments,
                'payment_date': '2024-01-05',
                'scheduled_date': '2024-01-05',
                'principal_component': 1511.67,
                'interest_component': 7166.67,
                'total_amount': 8678.34,
                'payment_type': 'EMI',
                'payment_method': 'Auto Debit',
                'charges': 0,
                'balance_remaining': 998488.33,
                'status': 'PAID'
            }

            Payment.create(payment_data)

            # Retrieve payments
            payments = Payment.get_by_loan(loan_with_payments)
            assert len(payments) == 1
            assert payments[0].loan_id == loan_with_payments

    def test_balance_cascade_recalculation(self, app, loan_with_payments):
        """Test that balance cascade recalculation works."""
        with app.app_context():
            # Create first payment
            payment1_data = {
                'loan_id': loan_with_payments,
                'payment_date': '2024-01-05',
                'scheduled_date': '2024-01-05',
                'principal_component': 1511.67,
                'interest_component': 7166.67,
                'total_amount': 8678.34,
                'payment_type': 'EMI',
                'payment_method': 'Auto Debit',
                'charges': 0,
                'balance_remaining': 998488.33,
                'status': 'PAID'
            }

            Payment.create(payment1_data)

            # Create second payment
            payment2_data = {
                'loan_id': loan_with_payments,
                'payment_date': '2024-02-05',
                'scheduled_date': '2024-02-05',
                'principal_component': 1522.42,
                'interest_component': 7155.92,
                'total_amount': 8678.34,
                'payment_type': 'EMI',
                'payment_method': 'Auto Debit',
                'charges': 0,
                'balance_remaining': 996965.91,
                'status': 'PAID'
            }

            Payment.create(payment2_data)

            # Verify balances are calculated correctly
            payments = Payment.get_by_loan(loan_with_payments)
            assert len(payments) == 2

            # First payment balance should be principal - first payment principal
            expected_balance1 = 1000000 - 1511.67
            actual_balance1 = float(payments[1].balance_remaining)  # Sorted DESC
            assert abs(actual_balance1 - expected_balance1) < 1  # Allow small rounding difference


class TestUtilityFunctions:
    """Test utility functions are available and working."""

    def test_loan_calculator_available(self):
        """Test that LoanCalculator is available."""
        from utils.calculations import LoanCalculator

        # Test EMI calculation
        emi = LoanCalculator.calculate_emi(1000000, 8.5, 240)
        assert emi > 0
        assert isinstance(emi, float)

    def test_amortization_schedule_available(self):
        """Test that AmortizationSchedule is available."""
        from utils.amortization import AmortizationSchedule

        loan_details = {
            'principal': 1000000,
            'annual_rate': 8.5,
            'tenure_months': 240,
            'emi': 8678,
            'start_date': '2024-01-01',
            'payment_frequency': 'MONTHLY'
        }

        amortization = AmortizationSchedule(loan_details)
        schedule = amortization.generate_standard_schedule()

        assert not schedule.empty
        assert len(schedule) > 0

    def test_dashboard_metrics_available(self):
        """Test that DashboardMetrics is available."""
        from utils.metrics import DashboardMetrics

        # This should not raise an error
        assert DashboardMetrics is not None

    def test_visualization_available(self):
        """Test that ChartGenerator is available."""
        from utils.visualization import ChartGenerator

        # This should not raise an error
        assert ChartGenerator is not None


class TestDatabaseBackup:
    """Test database backup functionality."""

    def test_backup_creation(self, app, db):
        """Test that database backup can be created."""
        import os

        # Create backup
        backup_path = db.backup_database()

        # Verify backup file exists
        assert os.path.exists(backup_path)
        assert backup_path.endswith('.db')

        # Cleanup
        os.remove(backup_path)


class TestTableCounts:
    """Test table count functions."""

    def test_get_table_count(self, app, db):
        """Test getting row count for a table."""
        # Initially should be 0
        count = db.get_table_count('loans')
        assert count == 0

        # Create a loan
        with app.app_context():
            loan_data = {
                'loan_name': 'Test Loan',
                'loan_type': 'HOME',
                'bank_name': 'Test Bank',
                'principal_amount': 1000000,
                'sanctioned_amount': 1000000,
                'interest_rate': 8.5,
                'rate_type': 'FIXED',
                'loan_term_months': 240,
                'start_date': '2024-01-01',
                'emi_amount': 8678,
                'payment_frequency': 'MONTHLY',
                'status': 'ACTIVE'
            }
            Loan.create(loan_data)

        # Count should be 1
        count = db.get_table_count('loans')
        assert count == 1

    def test_invalid_table_name(self, app, db):
        """Test that invalid table names are rejected."""
        with pytest.raises(ValueError):
            db.get_table_count('invalid_table')
