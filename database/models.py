"""
Data models and CRUD operations for the loan dashboard.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
from database.db_manager import get_db_manager


@dataclass
class Loan:
    """Loan data model."""
    loan_id: Optional[int] = None
    loan_name: str = ""
    loan_type: str = ""
    bank_name: str = ""
    principal_amount: float = 0.0
    sanctioned_amount: float = 0.0
    interest_rate: float = 0.0
    rate_type: str = "FIXED"
    loan_term_months: int = 0
    start_date: str = ""
    emi_amount: float = 0.0
    payment_frequency: str = "MONTHLY"
    status: str = "ACTIVE"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @staticmethod
    def create(loan_data: Dict[str, Any]) -> int:
        """
        Create a new loan record.

        Args:
            loan_data: Dictionary containing loan details

        Returns:
            loan_id of created record
        """
        db = get_db_manager()

        query = """
        INSERT INTO loans (
            loan_name, loan_type, bank_name, principal_amount,
            sanctioned_amount, interest_rate, rate_type, loan_term_months,
            start_date, emi_amount, payment_frequency, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            loan_data['loan_name'],
            loan_data['loan_type'],
            loan_data['bank_name'],
            loan_data['principal_amount'],
            loan_data['sanctioned_amount'],
            loan_data['interest_rate'],
            loan_data['rate_type'],
            loan_data['loan_term_months'],
            loan_data['start_date'],
            loan_data['emi_amount'],
            loan_data['payment_frequency'],
            loan_data.get('status', 'ACTIVE')
        )

        return db.execute_query(query, params)

    @staticmethod
    def get_by_id(loan_id: int) -> Optional['Loan']:
        """Get loan by ID."""
        db = get_db_manager()
        query = "SELECT * FROM loans WHERE loan_id = ?"
        result = db.fetch_one(query, (loan_id,))

        if result:
            return Loan(**dict(result))
        return None

    @staticmethod
    def get_all(status: Optional[str] = None) -> List['Loan']:
        """
        Get all loans, optionally filtered by status.

        Args:
            status: Filter by loan status (ACTIVE, CLOSED, PENDING)

        Returns:
            List of Loan objects
        """
        db = get_db_manager()

        if status:
            query = "SELECT * FROM loans WHERE status = ? ORDER BY created_at DESC"
            results = db.fetch_all(query, (status,))
        else:
            query = "SELECT * FROM loans ORDER BY created_at DESC"
            results = db.fetch_all(query)

        return [Loan(**dict(row)) for row in results]

    @staticmethod
    def update(loan_id: int, loan_data: Dict[str, Any]) -> int:
        """
        Update existing loan record.

        Args:
            loan_id: ID of loan to update
            loan_data: Dictionary containing updated fields

        Returns:
            Number of rows updated
        """
        db = get_db_manager()

        query = """
        UPDATE loans SET
            loan_name = ?,
            loan_type = ?,
            bank_name = ?,
            principal_amount = ?,
            sanctioned_amount = ?,
            interest_rate = ?,
            rate_type = ?,
            loan_term_months = ?,
            start_date = ?,
            emi_amount = ?,
            payment_frequency = ?,
            status = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE loan_id = ?
        """

        params = (
            loan_data['loan_name'],
            loan_data['loan_type'],
            loan_data['bank_name'],
            loan_data['principal_amount'],
            loan_data['sanctioned_amount'],
            loan_data['interest_rate'],
            loan_data['rate_type'],
            loan_data['loan_term_months'],
            loan_data['start_date'],
            loan_data['emi_amount'],
            loan_data['payment_frequency'],
            loan_data['status'],
            loan_id
        )

        return db.execute_query(query, params)

    @staticmethod
    def delete(loan_id: int) -> int:
        """Delete loan by ID."""
        db = get_db_manager()
        query = "DELETE FROM loans WHERE loan_id = ?"
        return db.execute_query(query, (loan_id,))


@dataclass
class Payment:
    """Payment data model."""
    payment_id: Optional[int] = None
    loan_id: int = 0
    payment_date: str = ""
    scheduled_date: str = ""
    principal_component: float = 0.0
    interest_component: float = 0.0
    total_amount: float = 0.0
    payment_type: str = "EMI"
    payment_method: str = ""
    charges: float = 0.0
    balance_remaining: float = 0.0
    status: str = "PAID"
    notes: str = ""
    created_at: Optional[str] = None

    @staticmethod
    def create(payment_data: Dict[str, Any]) -> int:
        """Create a new payment record and recalculate balance cascade."""
        db = get_db_manager()

        loan_id = payment_data['loan_id']

        query = """
        INSERT INTO payments (
            loan_id, payment_date, scheduled_date, principal_component,
            interest_component, total_amount, payment_type, payment_method,
            charges, balance_remaining, status, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            loan_id,
            payment_data['payment_date'],
            payment_data.get('scheduled_date', payment_data['payment_date']),
            payment_data['principal_component'],
            payment_data['interest_component'],
            payment_data['total_amount'],
            payment_data.get('payment_type', 'EMI'),
            payment_data.get('payment_method', ''),
            payment_data.get('charges', 0.0),
            payment_data['balance_remaining'],
            payment_data.get('status', 'PAID'),
            payment_data.get('notes', '')
        )

        payment_id = db.execute_query(query, params)

        # Recalculate balance cascade for all payments
        Payment.recalculate_balance_cascade(loan_id)

        return payment_id

    @staticmethod
    def get_by_loan(loan_id: int) -> List['Payment']:
        """Get all payments for a specific loan."""
        db = get_db_manager()
        query = """
        SELECT * FROM payments
        WHERE loan_id = ?
        ORDER BY payment_date DESC
        """
        results = db.fetch_all(query, (loan_id,))
        return [Payment(**dict(row)) for row in results]

    @staticmethod
    def get_by_id(payment_id: int) -> Optional['Payment']:
        """Get payment by ID."""
        db = get_db_manager()
        query = "SELECT * FROM payments WHERE payment_id = ?"
        result = db.fetch_one(query, (payment_id,))

        if result:
            return Payment(**dict(result))
        return None

    @staticmethod
    def update(payment_id: int, payment_data: Dict[str, Any]) -> int:
        """
        Update existing payment record and recalculate balance cascade.

        Args:
            payment_id: ID of payment to update
            payment_data: Dictionary containing updated fields

        Returns:
            Number of rows updated
        """
        # Get the loan_id before updating
        payment = Payment.get_by_id(payment_id)
        if not payment:
            return 0

        loan_id = payment.loan_id

        db = get_db_manager()

        query = """
        UPDATE payments SET
            payment_date = ?,
            scheduled_date = ?,
            principal_component = ?,
            interest_component = ?,
            total_amount = ?,
            payment_type = ?,
            payment_method = ?,
            charges = ?,
            balance_remaining = ?,
            status = ?,
            notes = ?
        WHERE payment_id = ?
        """

        params = (
            payment_data['payment_date'],
            payment_data['scheduled_date'],
            payment_data['principal_component'],
            payment_data['interest_component'],
            payment_data['total_amount'],
            payment_data['payment_type'],
            payment_data['payment_method'],
            payment_data.get('charges', 0.0),
            payment_data['balance_remaining'],
            payment_data['status'],
            payment_data.get('notes', ''),
            payment_id
        )

        result = db.execute_query(query, params)

        # Recalculate balance cascade for all payments
        Payment.recalculate_balance_cascade(loan_id)

        return result

    @staticmethod
    def delete(payment_id: int) -> int:
        """Delete payment by ID."""
        # Get the payment info before deleting
        payment = Payment.get_by_id(payment_id)
        if not payment:
            return 0

        loan_id = payment.loan_id

        db = get_db_manager()
        query = "DELETE FROM payments WHERE payment_id = ?"
        result = db.execute_query(query, (payment_id,))

        # Recalculate balances for remaining payments
        Payment.recalculate_balance_cascade(loan_id)

        return result

    @staticmethod
    def recalculate_balance_cascade(loan_id: int) -> None:
        """
        Recalculate balance_remaining for all payments of a loan in chronological order.
        This ensures data integrity when payments are created, updated, or deleted.

        Args:
            loan_id: ID of the loan whose payments need recalculation
        """
        db = get_db_manager()

        # Get the loan's principal amount
        loan = Loan.get_by_id(loan_id)
        if not loan:
            return

        starting_balance = float(loan.principal_amount)

        # Get all payments for this loan in chronological order
        payments = db.fetch_all('''
            SELECT payment_id, principal_component
            FROM payments
            WHERE loan_id = ?
            ORDER BY payment_date ASC, payment_id ASC
        ''', (loan_id,))

        # Recalculate and update each payment's balance
        current_balance = starting_balance

        for payment_id, principal in payments:
            current_balance -= principal

            db.execute_query('''
                UPDATE payments
                SET balance_remaining = ?
                WHERE payment_id = ?
            ''', (current_balance, payment_id))


@dataclass
class InterestRateHistory:
    """Interest rate history data model."""
    rate_id: Optional[int] = None
    loan_id: int = 0
    effective_date: str = ""
    interest_rate: float = 0.0
    reason: str = ""
    created_at: Optional[str] = None

    @staticmethod
    def create(rate_data: Dict[str, Any]) -> int:
        """Create a new rate change record."""
        db = get_db_manager()

        query = """
        INSERT INTO interest_rate_history (
            loan_id, effective_date, interest_rate, reason
        ) VALUES (?, ?, ?, ?)
        """

        params = (
            rate_data['loan_id'],
            rate_data['effective_date'],
            rate_data['interest_rate'],
            rate_data.get('reason', '')
        )

        return db.execute_query(query, params)

    @staticmethod
    def get_by_loan(loan_id: int) -> List['InterestRateHistory']:
        """Get rate history for a specific loan."""
        db = get_db_manager()
        query = """
        SELECT * FROM interest_rate_history
        WHERE loan_id = ?
        ORDER BY effective_date DESC
        """
        results = db.fetch_all(query, (loan_id,))
        return [InterestRateHistory(**dict(row)) for row in results]


@dataclass
class LoanDisbursement:
    """Loan disbursement data model."""
    disbursement_id: Optional[int] = None
    loan_id: int = 0
    disbursement_date: str = ""
    amount: float = 0.0
    new_emi: float = 0.0
    created_at: Optional[str] = None

    @staticmethod
    def create(disbursement_data: Dict[str, Any]) -> int:
        """Create a new disbursement record."""
        db = get_db_manager()

        query = """
        INSERT INTO loan_disbursements (
            loan_id, disbursement_date, amount, new_emi
        ) VALUES (?, ?, ?, ?)
        """

        params = (
            disbursement_data['loan_id'],
            disbursement_data['disbursement_date'],
            disbursement_data['amount'],
            disbursement_data['new_emi']
        )

        return db.execute_query(query, params)

    @staticmethod
    def get_by_loan(loan_id: int) -> List['LoanDisbursement']:
        """Get all disbursements for a specific loan."""
        db = get_db_manager()
        query = """
        SELECT * FROM loan_disbursements
        WHERE loan_id = ?
        ORDER BY disbursement_date ASC
        """
        results = db.fetch_all(query, (loan_id,))
        return [LoanDisbursement(**dict(row)) for row in results]


@dataclass
class ForecastScenario:
    """Forecast scenario data model."""
    scenario_id: Optional[int] = None
    loan_id: int = 0
    scenario_name: str = ""
    prepayment_type: str = "LUMPSUM"
    prepayment_value: float = 0.0
    start_month: int = 0
    created_at: Optional[str] = None

    @staticmethod
    def create(scenario_data: Dict[str, Any]) -> int:
        """Create a new forecast scenario."""
        db = get_db_manager()

        query = """
        INSERT INTO forecast_scenarios (
            loan_id, scenario_name, prepayment_type, prepayment_value, start_month
        ) VALUES (?, ?, ?, ?, ?)
        """

        params = (
            scenario_data['loan_id'],
            scenario_data['scenario_name'],
            scenario_data['prepayment_type'],
            scenario_data['prepayment_value'],
            scenario_data['start_month']
        )

        return db.execute_query(query, params)

    @staticmethod
    def get_by_loan(loan_id: int) -> List['ForecastScenario']:
        """Get all scenarios for a specific loan."""
        db = get_db_manager()
        query = """
        SELECT * FROM forecast_scenarios
        WHERE loan_id = ?
        ORDER BY created_at DESC
        """
        results = db.fetch_all(query, (loan_id,))
        return [ForecastScenario(**dict(row)) for row in results]

    @staticmethod
    def delete(scenario_id: int) -> int:
        """Delete scenario by ID."""
        db = get_db_manager()
        query = "DELETE FROM forecast_scenarios WHERE scenario_id = ?"
        return db.execute_query(query, (scenario_id,))
