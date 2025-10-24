"""
Metrics calculation utilities for dashboard analytics.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import pandas as pd
from database.models import Loan, Payment
from database.db_manager import get_db_manager


class DashboardMetrics:
    """Calculate various metrics for the dashboard."""

    @staticmethod
    def get_total_outstanding_balance() -> float:
        """
        Calculate total outstanding balance across all active and pending loans.

        Optimized version using a single SQL query with LEFT JOIN to avoid N+1 problem.

        Returns:
            Total outstanding balance
        """
        db = get_db_manager()

        # Single query with LEFT JOIN and subquery to get latest payment per loan
        query = """
        SELECT
            l.loan_id,
            l.principal_amount,
            COALESCE(
                (SELECT p.balance_remaining
                 FROM payments p
                 WHERE p.loan_id = l.loan_id
                 ORDER BY p.payment_date DESC, p.payment_id DESC
                 LIMIT 1),
                l.principal_amount
            ) as outstanding
        FROM loans l
        WHERE l.status IN ('ACTIVE', 'PENDING')
        """

        results = db.fetch_all(query)

        if not results:
            return 0.0

        total_outstanding = sum(float(row['outstanding']) for row in results)
        return round(total_outstanding, 2)

    @staticmethod
    def get_monthly_payment_obligation() -> float:
        """
        Calculate total monthly EMI obligation for all active and pending loans.

        Optimized version using a single SQL query with SUM aggregation.

        Returns:
            Total monthly EMI amount
        """
        db = get_db_manager()

        query = """
        SELECT COALESCE(SUM(emi_amount), 0) as total_emi
        FROM loans
        WHERE status IN ('ACTIVE', 'PENDING')
        """

        result = db.fetch_one(query)

        if result and result['total_emi']:
            return round(float(result['total_emi']), 2)

        return 0.0

    @staticmethod
    def get_interest_paid_current_year() -> float:
        """
        Calculate total interest paid in the current year.

        Returns:
            Total interest paid this year
        """
        db = get_db_manager()
        current_year = datetime.now().year

        query = """
        SELECT SUM(interest_component) as total_interest
        FROM payments
        WHERE strftime('%Y', payment_date) = ?
        AND status = 'PAID'
        """

        result = db.fetch_one(query, (str(current_year),))

        if result and result['total_interest']:
            return round(float(result['total_interest']), 2)

        return 0.0

    @staticmethod
    def get_next_payment_due() -> Optional[Dict]:
        """
        Get details of the next upcoming payment.

        Returns:
            Dictionary with next payment details or None
        """
        db = get_db_manager()
        today = date.today().strftime('%Y-%m-%d')

        query = """
        SELECT p.*, l.loan_name, l.bank_name
        FROM payments p
        JOIN loans l ON p.loan_id = l.loan_id
        WHERE p.scheduled_date >= ?
        AND p.status = 'PENDING'
        ORDER BY p.scheduled_date ASC
        LIMIT 1
        """

        result = db.fetch_one(query, (today,))

        if result:
            return dict(result)

        return None

    @staticmethod
    def get_loan_summary_cards() -> List[Dict]:
        """
        Get summary cards data for all active and pending loans.

        Optimized version using a single SQL query with subqueries to avoid N+1 problem.

        Returns:
            List of dictionaries with loan summary data
        """
        db = get_db_manager()
        today = date.today().strftime('%Y-%m-%d')

        # Single query with subqueries for latest balance and next payment
        query = """
        SELECT
            l.loan_id,
            l.loan_name,
            l.bank_name,
            l.loan_type,
            l.principal_amount,
            l.interest_rate,
            l.rate_type,
            l.emi_amount,
            COALESCE(
                (SELECT p.balance_remaining
                 FROM payments p
                 WHERE p.loan_id = l.loan_id
                 ORDER BY p.payment_date DESC, p.payment_id DESC
                 LIMIT 1),
                l.principal_amount
            ) as outstanding,
            (SELECT p.scheduled_date
             FROM payments p
             WHERE p.loan_id = l.loan_id
               AND p.scheduled_date >= ?
               AND p.status = 'PENDING'
             ORDER BY p.scheduled_date ASC
             LIMIT 1) as next_payment
        FROM loans l
        WHERE l.status IN ('ACTIVE', 'PENDING')
        ORDER BY l.created_at DESC
        """

        results = db.fetch_all(query, (today,))

        loan_cards = []
        for row in results:
            outstanding = float(row['outstanding'])
            principal = float(row['principal_amount'])
            total_paid = principal - outstanding
            progress = (total_paid / principal * 100) if principal > 0 else 0

            loan_cards.append({
                'loan_id': row['loan_id'],
                'loan_name': row['loan_name'],
                'bank_name': row['bank_name'],
                'loan_type': row['loan_type'],
                'principal': principal,
                'outstanding': outstanding,
                'progress': round(progress, 1),
                'interest_rate': float(row['interest_rate']),
                'rate_type': row['rate_type'],
                'emi': float(row['emi_amount']),
                'next_payment': row['next_payment']
            })

        return loan_cards

    @staticmethod
    def get_payment_timeline_data(months: int = 12) -> pd.DataFrame:
        """
        Get payment timeline data for the last N months.

        Args:
            months: Number of months to include

        Returns:
            DataFrame with payment timeline data
        """
        db = get_db_manager()
        start_date = (datetime.now() - relativedelta(months=months)).strftime('%Y-%m-%d')

        query = """
        SELECT
            payment_date as date,
            SUM(principal_component) as principal,
            SUM(interest_component) as interest,
            SUM(total_amount) as total
        FROM payments
        WHERE payment_date >= ?
        AND status = 'PAID'
        GROUP BY payment_date
        ORDER BY payment_date ASC
        """

        results = db.fetch_all(query, (start_date,))

        if not results:
            return pd.DataFrame()

        data = [dict(row) for row in results]
        return pd.DataFrame(data)

    @staticmethod
    def get_total_principal_vs_interest() -> Tuple[float, float]:
        """
        Get total principal and interest paid across all loans.

        Returns:
            Tuple of (total_principal_paid, total_interest_paid)
        """
        db = get_db_manager()

        query = """
        SELECT
            SUM(principal_component) as total_principal,
            SUM(interest_component) as total_interest
        FROM payments
        WHERE status = 'PAID'
        """

        result = db.fetch_one(query)

        if result:
            principal = float(result['total_principal']) if result['total_principal'] else 0.0
            interest = float(result['total_interest']) if result['total_interest'] else 0.0
            return (round(principal, 2), round(interest, 2))

        return (0.0, 0.0)

    @staticmethod
    def get_loan_comparison_data() -> List[Dict]:
        """
        Get comparison data for all loans.

        Optimized version using a single SQL query with LEFT JOIN and aggregation.

        Returns:
            List of dictionaries with loan comparison data
        """
        db = get_db_manager()

        # Single query with LEFT JOIN and SUM aggregation
        query = """
        SELECT
            l.loan_id,
            l.loan_name,
            l.loan_type,
            l.status,
            l.principal_amount,
            COALESCE(SUM(CASE WHEN p.status = 'PAID' THEN p.interest_component ELSE 0 END), 0) as total_interest
        FROM loans l
        LEFT JOIN payments p ON l.loan_id = p.loan_id
        GROUP BY l.loan_id, l.loan_name, l.loan_type, l.status, l.principal_amount
        ORDER BY l.created_at DESC
        """

        results = db.fetch_all(query)

        comparison_data = []
        for row in results:
            comparison_data.append({
                'loan_name': row['loan_name'],
                'principal': float(row['principal_amount']),
                'interest': float(row['total_interest']),
                'loan_type': row['loan_type'],
                'status': row['status']
            })

        return comparison_data

    @staticmethod
    def get_year_wise_interest() -> pd.DataFrame:
        """
        Get year-wise interest payment summary.

        Returns:
            DataFrame with year and total interest
        """
        db = get_db_manager()

        query = """
        SELECT
            strftime('%Y', payment_date) as year,
            SUM(interest_component) as total_interest
        FROM payments
        WHERE status = 'PAID'
        GROUP BY year
        ORDER BY year DESC
        """

        results = db.fetch_all(query)

        if not results:
            return pd.DataFrame()

        data = [dict(row) for row in results]
        return pd.DataFrame(data)

    @staticmethod
    def get_payment_status_counts() -> Dict[str, int]:
        """
        Get count of payments by status.

        Returns:
            Dictionary with status counts
        """
        db = get_db_manager()

        query = """
        SELECT status, COUNT(*) as count
        FROM payments
        GROUP BY status
        """

        results = db.fetch_all(query)

        if not results:
            return {}

        return {row['status']: row['count'] for row in results}

    @staticmethod
    def get_monthly_obligation_forecast(months: int = 12) -> pd.DataFrame:
        """
        Forecast monthly payment obligations.

        Optimized version using a single SQL query for total EMI.

        Args:
            months: Number of months to forecast

        Returns:
            DataFrame with forecasted monthly obligations
        """
        db = get_db_manager()

        # Get total EMI in one query
        query = """
        SELECT COALESCE(SUM(emi_amount), 0) as total_emi
        FROM loans
        WHERE status IN ('ACTIVE', 'PENDING')
        """

        result = db.fetch_one(query)
        total_emi = float(result['total_emi']) if result and result['total_emi'] else 0.0

        if total_emi == 0:
            return pd.DataFrame()

        # Create forecast for next N months
        forecast_data = []
        start_date = datetime.now()

        for i in range(months):
            forecast_date = start_date + relativedelta(months=i)
            month = forecast_date.month
            year = forecast_date.year

            forecast_data.append({
                'month': month,
                'year': year,
                'total_emi': total_emi,
                'date': forecast_date.strftime('%Y-%m-%d')
            })

        return pd.DataFrame(forecast_data)

    @staticmethod
    def calculate_loan_statistics(loan_id: int) -> Dict:
        """
        Calculate detailed statistics for a specific loan.

        Args:
            loan_id: ID of the loan

        Returns:
            Dictionary with loan statistics
        """
        loan = Loan.get_by_id(loan_id)
        if not loan:
            return {}

        payments = Payment.get_by_loan(loan_id)

        # Calculate various metrics
        total_paid_principal = sum(
            float(p.principal_component) for p in payments
            if p.status == 'PAID'
        )

        total_paid_interest = sum(
            float(p.interest_component) for p in payments
            if p.status == 'PAID'
        )

        outstanding = (
            payments[0].balance_remaining if payments
            else loan.principal_amount
        )

        payments_made = len([p for p in payments if p.status == 'PAID'])
        payments_pending = len([p for p in payments if p.status == 'PENDING'])
        payments_missed = len([p for p in payments if p.status == 'MISSED'])

        return {
            'loan_name': loan.loan_name,
            'original_principal': float(loan.principal_amount),
            'outstanding': outstanding,
            'total_paid_principal': total_paid_principal,
            'total_paid_interest': total_paid_interest,
            'total_paid': total_paid_principal + total_paid_interest,
            'payments_made': payments_made,
            'payments_pending': payments_pending,
            'payments_missed': payments_missed,
            'progress_percentage': (total_paid_principal / float(loan.principal_amount) * 100)
                if loan.principal_amount > 0 else 0
        }
