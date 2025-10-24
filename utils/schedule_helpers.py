"""
Helper functions for generating and managing payment schedules.
"""

from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from typing import List, Dict, Optional
import pandas as pd
from database.models import Loan, Payment
from utils.calculations import LoanCalculator
from utils.amortization import AmortizationSchedule


class ScheduleHelper:
    """Helper functions for payment schedule operations."""

    @staticmethod
    def generate_payment_schedule(loan_id: int) -> pd.DataFrame:
        """
        Generate complete payment schedule for a loan.

        Args:
            loan_id: ID of the loan

        Returns:
            DataFrame with payment schedule
        """
        loan = Loan.get_by_id(loan_id)
        if not loan:
            return pd.DataFrame()

        # Prepare loan details for amortization
        loan_details = {
            'principal': float(loan.principal_amount),
            'annual_rate': float(loan.interest_rate),
            'tenure_months': int(loan.loan_term_months),
            'emi': float(loan.emi_amount),
            'start_date': loan.start_date,
            'payment_frequency': loan.payment_frequency
        }

        # Generate schedule
        amortization = AmortizationSchedule(loan_details)
        schedule = amortization.generate_standard_schedule()

        return schedule

    @staticmethod
    def generate_schedule_with_actuals(loan_id: int) -> pd.DataFrame:
        """
        Generate payment schedule with actual payment data merged.

        Args:
            loan_id: ID of the loan

        Returns:
            DataFrame with scheduled and actual payments
        """
        # Get base schedule
        schedule = ScheduleHelper.generate_payment_schedule(loan_id)

        if schedule.empty:
            return pd.DataFrame()

        # Get actual payments
        payments = Payment.get_by_loan(loan_id)

        # Convert payments to DataFrame
        if payments:
            payment_data = []
            for payment in payments:
                payment_data.append({
                    'payment_date': payment.payment_date,
                    'actual_principal': payment.principal_component,
                    'actual_interest': payment.interest_component,
                    'actual_total': payment.total_amount,
                    'status': payment.status,
                    'payment_type': payment.payment_type
                })

            payments_df = pd.DataFrame(payment_data)

            # Merge with schedule based on dates
            schedule['scheduled_date'] = schedule['date']
            merged = schedule.merge(
                payments_df,
                left_on='scheduled_date',
                right_on='payment_date',
                how='left'
            )

            return merged
        else:
            # No actual payments yet, add empty columns
            schedule['payment_date'] = None
            schedule['actual_principal'] = None
            schedule['actual_interest'] = None
            schedule['actual_total'] = None
            schedule['status'] = 'PENDING'
            schedule['payment_type'] = None

            return schedule

    @staticmethod
    def create_scheduled_payments(loan_id: int) -> int:
        """
        Create scheduled payment records for a loan.

        Args:
            loan_id: ID of the loan

        Returns:
            Number of payment records created
        """
        loan = Loan.get_by_id(loan_id)
        if not loan:
            return 0

        # Check if payments already exist
        existing_payments = Payment.get_by_loan(loan_id)
        if existing_payments:
            return 0  # Don't create if payments already exist

        # Generate schedule
        schedule = ScheduleHelper.generate_payment_schedule(loan_id)

        if schedule.empty:
            return 0

        # Create payment records
        count = 0
        for idx, row in schedule.iterrows():
            payment_data = {
                'loan_id': loan_id,
                'payment_date': row['date'],
                'scheduled_date': row['date'],
                'principal_component': row['principal'],
                'interest_component': row['interest'],
                'total_amount': row['emi'],
                'payment_type': 'EMI',
                'payment_method': '',
                'charges': 0.0,
                'balance_remaining': row['balance'],
                'status': 'PENDING',
                'notes': 'Auto-generated scheduled payment'
            }

            Payment.create(payment_data)
            count += 1

        return count

    @staticmethod
    def get_next_scheduled_payment(loan_id: int) -> Optional[Dict]:
        """
        Get the next scheduled payment for a loan.

        Args:
            loan_id: ID of the loan

        Returns:
            Dictionary with payment details or None
        """
        from database.db_manager import get_db_manager

        db = get_db_manager()
        today = date.today().strftime('%Y-%m-%d')

        query = """
        SELECT *
        FROM payments
        WHERE loan_id = ?
        AND scheduled_date >= ?
        AND status = 'PENDING'
        ORDER BY scheduled_date ASC
        LIMIT 1
        """

        result = db.fetch_one(query, (loan_id, today))

        if result:
            return dict(result)

        return None

    @staticmethod
    def get_upcoming_payments(loan_id: int, count: int = 5) -> List[Dict]:
        """
        Get upcoming scheduled payments.

        Args:
            loan_id: ID of the loan
            count: Number of upcoming payments to retrieve

        Returns:
            List of payment dictionaries
        """
        from database.db_manager import get_db_manager

        db = get_db_manager()
        today = date.today().strftime('%Y-%m-%d')

        query = """
        SELECT *
        FROM payments
        WHERE loan_id = ?
        AND scheduled_date >= ?
        AND status = 'PENDING'
        ORDER BY scheduled_date ASC
        LIMIT ?
        """

        results = db.fetch_all(query, (loan_id, today, count))

        return [dict(row) for row in results]

    @staticmethod
    def get_payment_history(
        loan_id: int,
        limit: Optional[int] = None,
        status: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get payment history for a loan.

        Args:
            loan_id: ID of the loan
            limit: Maximum number of records to retrieve
            status: Filter by payment status

        Returns:
            DataFrame with payment history
        """
        from database.db_manager import get_db_manager

        db = get_db_manager()

        if status:
            query = """
            SELECT *
            FROM payments
            WHERE loan_id = ?
            AND status = ?
            ORDER BY payment_date DESC
            """
            params = (loan_id, status)
        else:
            query = """
            SELECT *
            FROM payments
            WHERE loan_id = ?
            ORDER BY payment_date DESC
            """
            params = (loan_id,)

        if limit:
            query += f" LIMIT {limit}"

        results = db.fetch_all(query, params)

        if not results:
            return pd.DataFrame()

        data = [dict(row) for row in results]
        return pd.DataFrame(data)

    @staticmethod
    def calculate_remaining_payments(loan_id: int) -> Dict:
        """
        Calculate remaining payment statistics.

        Args:
            loan_id: ID of the loan

        Returns:
            Dictionary with remaining payment statistics
        """
        from database.db_manager import get_db_manager

        db = get_db_manager()

        # Get counts
        query = """
        SELECT
            COUNT(CASE WHEN status = 'PAID' THEN 1 END) as paid_count,
            COUNT(CASE WHEN status = 'PENDING' THEN 1 END) as pending_count,
            COUNT(CASE WHEN status = 'MISSED' THEN 1 END) as missed_count
        FROM payments
        WHERE loan_id = ?
        """

        result = db.fetch_one(query, (loan_id,))

        if not result:
            return {
                'paid_count': 0,
                'pending_count': 0,
                'missed_count': 0,
                'total_count': 0
            }

        return {
            'paid_count': result['paid_count'] or 0,
            'pending_count': result['pending_count'] or 0,
            'missed_count': result['missed_count'] or 0,
            'total_count': (result['paid_count'] or 0) +
                          (result['pending_count'] or 0) +
                          (result['missed_count'] or 0)
        }

    @staticmethod
    def mark_payment_as_paid(
        payment_id: int,
        actual_date: str,
        actual_amount: Optional[float] = None,
        payment_method: Optional[str] = None,
        charges: float = 0.0,
        notes: str = ""
    ) -> bool:
        """
        Mark a scheduled payment as paid.

        Args:
            payment_id: ID of the payment
            actual_date: Actual payment date
            actual_amount: Actual amount paid (if different from scheduled)
            payment_method: Payment method used
            charges: Any additional charges
            notes: Payment notes

        Returns:
            True if successful, False otherwise
        """
        from database.db_manager import get_db_manager

        db = get_db_manager()

        # Build update query
        if actual_amount:
            query = """
            UPDATE payments
            SET payment_date = ?,
                status = 'PAID',
                total_amount = ?,
                payment_method = ?,
                charges = ?,
                notes = ?
            WHERE payment_id = ?
            """
            params = (actual_date, actual_amount, payment_method or '', charges, notes, payment_id)
        else:
            query = """
            UPDATE payments
            SET payment_date = ?,
                status = 'PAID',
                payment_method = ?,
                charges = ?,
                notes = ?
            WHERE payment_id = ?
            """
            params = (actual_date, payment_method or '', charges, notes, payment_id)

        try:
            db.execute_query(query, params)
            return True
        except Exception:
            return False

    @staticmethod
    def generate_hybrid_schedule(loan_id: int) -> pd.DataFrame:
        """
        Generate hybrid payment schedule with actual + projected payments.
        - Past: Uses actual user-entered payment data (principal/interest breakdown)
        - Future: Uses formula-based projections from last balance

        Args:
            loan_id: ID of the loan

        Returns:
            DataFrame with hybrid schedule
        """
        loan = Loan.get_by_id(loan_id)
        if not loan:
            return pd.DataFrame()

        # Get actual payments (PAID only)
        payments = Payment.get_by_loan(loan_id)
        paid_payments = [p for p in payments if p.status == 'PAID'] if payments else []

        schedule_data = []

        # Calculate months from loan start for each payment
        loan_start = datetime.strptime(loan.start_date, '%Y-%m-%d').date()

        # Part 1: Add actual paid payments (user-entered data)
        for idx, payment in enumerate(paid_payments, 1):
            payment_date = datetime.strptime(payment.payment_date, '%Y-%m-%d').date()
            # Calculate month number from loan start
            months_diff = (payment_date.year - loan_start.year) * 12 + (payment_date.month - loan_start.month)
            month_number = max(1, months_diff + 1)  # Ensure minimum of 1

            schedule_data.append({
                'payment_number': idx,
                'month': month_number,
                'date': payment.payment_date,
                'scheduled_date': payment.scheduled_date,
                'emi': payment.total_amount,
                'principal': payment.principal_component,
                'interest': payment.interest_component,
                'balance': payment.balance_remaining,
                'payment_type': payment.payment_type,
                'status': 'PAID (Actual)',
                'data_source': 'Actual'
            })

        # Part 2: Generate projected payments for future
        if paid_payments:
            # Get last payment details
            last_payment = paid_payments[0]  # Most recent (sorted by date DESC)
            current_balance = float(last_payment.balance_remaining)
            last_date_str = last_payment.payment_date
            last_date = datetime.strptime(last_date_str, '%Y-%m-%d').date()
            payment_number_start = len(paid_payments) + 1
        else:
            # No payments yet, start from loan details
            current_balance = float(loan.principal_amount)
            last_date = datetime.strptime(loan.start_date, '%Y-%m-%d').date()
            payment_number_start = 1

        # Get latest interest rate from rate history
        from database.models import InterestRateHistory
        rate_history = InterestRateHistory.get_by_loan(loan_id)
        if rate_history:
            current_rate = float(rate_history[0].interest_rate)  # Most recent rate
        else:
            current_rate = float(loan.interest_rate)

        # Calculate remaining months
        months_paid = len(paid_payments)
        remaining_months = int(loan.loan_term_months) - months_paid

        # Generate projected schedule if balance remaining
        if current_balance > 0 and remaining_months > 0:
            current_emi = float(loan.emi_amount)
            monthly_rate = current_rate / (12 * 100)

            for month in range(remaining_months):
                payment_number = payment_number_start + month

                # Calculate next payment date
                next_date = last_date + relativedelta(months=month+1)

                # Calculate month number from loan start
                months_from_start = (next_date.year - loan_start.year) * 12 + (next_date.month - loan_start.month)
                month_number = max(1, months_from_start + 1)

                # Calculate interest and principal
                interest_amount = current_balance * monthly_rate
                principal_amount = current_emi - interest_amount

                # Ensure we don't overpay on the last payment
                if principal_amount > current_balance:
                    principal_amount = current_balance
                    interest_amount = current_emi - principal_amount

                # Update balance
                current_balance = max(0, current_balance - principal_amount)

                schedule_data.append({
                    'payment_number': payment_number,
                    'month': month_number,
                    'date': next_date.strftime('%Y-%m-%d'),
                    'scheduled_date': next_date.strftime('%Y-%m-%d'),
                    'emi': current_emi,
                    'principal': round(principal_amount, 2),
                    'interest': round(interest_amount, 2),
                    'balance': round(current_balance, 2),
                    'payment_type': 'EMI',
                    'status': 'PROJECTED',
                    'data_source': 'Formula-based'
                })

                # Stop if balance reaches zero
                if current_balance <= 0:
                    break

        return pd.DataFrame(schedule_data)

    @staticmethod
    def get_schedule_summary(loan_id: int) -> Dict:
        """
        Get summary of payment schedule.

        Args:
            loan_id: ID of the loan

        Returns:
            Dictionary with schedule summary
        """
        schedule = ScheduleHelper.generate_payment_schedule(loan_id)

        if schedule.empty:
            return {}

        total_interest = schedule['interest'].sum()
        total_principal = schedule['principal'].sum()
        total_amount = schedule['emi'].sum()
        tenure_months = schedule['month'].max()

        return {
            'total_interest': round(total_interest, 2),
            'total_principal': round(total_principal, 2),
            'total_amount': round(total_amount, 2),
            'tenure_months': tenure_months,
            'number_of_payments': len(schedule)
        }
