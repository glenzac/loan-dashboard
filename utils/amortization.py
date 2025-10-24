"""
Amortization schedule generation and management.
"""

import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import Dict, List, Optional, Tuple
from utils.calculations import LoanCalculator
from config.constants import MONTHS_IN_YEAR


class AmortizationSchedule:
    """Generate and manage amortization schedules for loans."""

    def __init__(self, loan_details: Dict):
        """
        Initialize with loan details.

        Args:
            loan_details: Dictionary containing:
                - principal: Loan amount
                - annual_rate: Interest rate (percentage)
                - tenure_months: Loan tenure in months
                - emi: EMI amount
                - start_date: Loan start date (YYYY-MM-DD)
                - payment_frequency: MONTHLY, QUARTERLY, or ANNUALLY
        """
        self.principal = loan_details['principal']
        self.annual_rate = loan_details['annual_rate']
        self.tenure_months = loan_details['tenure_months']
        self.emi = loan_details['emi']
        self.start_date = datetime.strptime(loan_details['start_date'], '%Y-%m-%d')
        self.payment_frequency = loan_details.get('payment_frequency', 'MONTHLY')
        self.frequency_months = LoanCalculator.get_payment_frequency_multiplier(
            self.payment_frequency
        )

    def generate_standard_schedule(self) -> pd.DataFrame:
        """
        Generate standard amortization schedule.

        Returns:
            DataFrame with columns: month, date, emi, principal, interest, balance
        """
        schedule_data = []
        outstanding = self.principal
        payment_number = 0

        # Calculate total number of payments
        total_payments = self.tenure_months // self.frequency_months
        if self.tenure_months % self.frequency_months > 0:
            total_payments += 1

        for payment in range(total_payments):
            if outstanding <= 0:
                break

            payment_number += 1
            month_number = payment * self.frequency_months + self.frequency_months
            payment_date = self.start_date + relativedelta(months=month_number)

            # Split payment into principal and interest
            principal_component, interest_component = LoanCalculator.split_payment(
                self.emi,
                outstanding,
                self.annual_rate
            )

            # Handle final payment
            if principal_component > outstanding:
                principal_component = outstanding
                actual_emi = principal_component + interest_component
            else:
                actual_emi = self.emi

            # Update outstanding balance
            outstanding -= principal_component

            if outstanding < 0.01:  # Handle floating point precision
                outstanding = 0

            schedule_data.append({
                'payment_number': payment_number,
                'month': month_number,
                'date': payment_date.strftime('%Y-%m-%d'),
                'emi': round(actual_emi, 2),
                'principal': round(principal_component, 2),
                'interest': round(interest_component, 2),
                'balance': round(outstanding, 2)
            })

        return pd.DataFrame(schedule_data)

    def apply_prepayments(
        self,
        prepayments: List[Dict]
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Apply prepayments to schedule.

        Args:
            prepayments: List of prepayment dictionaries with:
                - month: Month number when prepayment is made
                - amount: Prepayment amount

        Returns:
            Tuple of (modified_schedule, summary_metrics)
        """
        schedule_data = []
        outstanding = self.principal
        payment_number = 0
        total_prepayment = 0

        # Sort prepayments by month
        prepayments_dict = {p['month']: p['amount'] for p in prepayments}

        # Calculate total number of payments (will be reduced by prepayments)
        max_payments = self.tenure_months // self.frequency_months + 1

        for payment in range(max_payments):
            if outstanding <= 0.01:
                break

            payment_number += 1
            month_number = payment * self.frequency_months + self.frequency_months
            payment_date = self.start_date + relativedelta(months=month_number)

            # Split payment into principal and interest
            principal_component, interest_component = LoanCalculator.split_payment(
                self.emi,
                outstanding,
                self.annual_rate
            )

            # Handle final payment
            if principal_component > outstanding:
                principal_component = outstanding
                actual_emi = principal_component + interest_component
            else:
                actual_emi = self.emi

            # Update outstanding balance
            outstanding -= principal_component

            # Apply prepayment if scheduled for this month
            prepayment_amount = 0
            if month_number in prepayments_dict:
                prepayment_amount = prepayments_dict[month_number]
                outstanding -= prepayment_amount
                total_prepayment += prepayment_amount

            if outstanding < 0.01:
                outstanding = 0

            schedule_data.append({
                'payment_number': payment_number,
                'month': month_number,
                'date': payment_date.strftime('%Y-%m-%d'),
                'emi': round(actual_emi, 2),
                'principal': round(principal_component, 2),
                'interest': round(interest_component, 2),
                'prepayment': round(prepayment_amount, 2),
                'balance': round(outstanding, 2)
            })

        df = pd.DataFrame(schedule_data)

        # Calculate summary metrics
        summary = self.get_summary_metrics(df)
        summary['total_prepayment'] = total_prepayment

        return df, summary

    def recalculate_with_rate_changes(
        self,
        rate_history: List[Dict]
    ) -> pd.DataFrame:
        """
        Recalculate schedule with floating rate changes.

        Args:
            rate_history: List of rate change dictionaries with:
                - month: Month number when rate changes
                - new_rate: New interest rate (percentage)

        Returns:
            DataFrame with modified schedule
        """
        schedule_data = []
        outstanding = self.principal
        payment_number = 0
        current_rate = self.annual_rate

        # Sort rate changes by month
        rate_changes = sorted(rate_history, key=lambda x: x['month'])
        rate_change_dict = {r['month']: r['new_rate'] for r in rate_changes}

        max_payments = self.tenure_months // self.frequency_months + 1

        for payment in range(max_payments):
            if outstanding <= 0.01:
                break

            payment_number += 1
            month_number = payment * self.frequency_months + self.frequency_months

            # Check if rate changes this month
            if month_number in rate_change_dict:
                current_rate = rate_change_dict[month_number]
                # Recalculate EMI with new rate
                remaining_months = self.tenure_months - month_number
                self.emi = LoanCalculator.calculate_emi(
                    outstanding,
                    current_rate,
                    remaining_months
                )

            payment_date = self.start_date + relativedelta(months=month_number)

            # Split payment with current rate
            principal_component, interest_component = LoanCalculator.split_payment(
                self.emi,
                outstanding,
                current_rate
            )

            # Handle final payment
            if principal_component > outstanding:
                principal_component = outstanding
                actual_emi = principal_component + interest_component
            else:
                actual_emi = self.emi

            outstanding -= principal_component

            if outstanding < 0.01:
                outstanding = 0

            schedule_data.append({
                'payment_number': payment_number,
                'month': month_number,
                'date': payment_date.strftime('%Y-%m-%d'),
                'interest_rate': round(current_rate, 2),
                'emi': round(actual_emi, 2),
                'principal': round(principal_component, 2),
                'interest': round(interest_component, 2),
                'balance': round(outstanding, 2)
            })

        return pd.DataFrame(schedule_data)

    def get_summary_metrics(self, schedule_df: Optional[pd.DataFrame] = None) -> Dict:
        """
        Calculate summary metrics from schedule.

        Args:
            schedule_df: Amortization schedule DataFrame (if None, generates standard)

        Returns:
            Dictionary containing:
                - total_interest: Total interest paid
                - total_amount: Total amount paid
                - actual_tenure: Actual tenure in months
                - total_payments: Number of payments
        """
        if schedule_df is None:
            schedule_df = self.generate_standard_schedule()

        total_interest = schedule_df['interest'].sum()
        total_emi = schedule_df['emi'].sum()

        if 'prepayment' in schedule_df.columns:
            total_prepayment = schedule_df['prepayment'].sum()
            total_amount = total_emi + total_prepayment
        else:
            total_prepayment = 0
            total_amount = total_emi

        actual_tenure = schedule_df['month'].max()
        total_payments = len(schedule_df)

        return {
            'total_interest': round(total_interest, 2),
            'total_amount': round(total_amount, 2),
            'actual_tenure': actual_tenure,
            'total_payments': total_payments,
            'principal': round(self.principal, 2),
            'total_prepayment': round(total_prepayment, 2)
        }

    def generate_monthly_breakup(self, schedule_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate month-by-month breakup for visualization.

        Args:
            schedule_df: Amortization schedule DataFrame

        Returns:
            DataFrame with monthly aggregations
        """
        # If payments are not monthly, expand to monthly view
        if self.payment_frequency != 'MONTHLY':
            monthly_data = []
            for idx, row in schedule_df.iterrows():
                # Distribute the payment across months
                months_in_period = self.frequency_months
                monthly_emi = row['emi'] / months_in_period
                monthly_principal = row['principal'] / months_in_period
                monthly_interest = row['interest'] / months_in_period

                for i in range(months_in_period):
                    month_num = row['month'] - self.frequency_months + i + 1
                    if month_num > 0:
                        monthly_data.append({
                            'month': month_num,
                            'emi': monthly_emi,
                            'principal': monthly_principal,
                            'interest': monthly_interest
                        })

            return pd.DataFrame(monthly_data)
        else:
            return schedule_df[['month', 'emi', 'principal', 'interest']].copy()

    @staticmethod
    def compare_schedules(
        base_schedule: pd.DataFrame,
        modified_schedule: pd.DataFrame
    ) -> Dict:
        """
        Compare two schedules and calculate differences.

        Args:
            base_schedule: Original amortization schedule
            modified_schedule: Modified schedule (with prepayments, etc.)

        Returns:
            Dictionary with comparison metrics
        """
        base_interest = base_schedule['interest'].sum()
        modified_interest = modified_schedule['interest'].sum()

        base_tenure = base_schedule['month'].max()
        modified_tenure = modified_schedule['month'].max()

        return {
            'interest_saved': round(base_interest - modified_interest, 2),
            'months_saved': base_tenure - modified_tenure,
            'base_interest': round(base_interest, 2),
            'modified_interest': round(modified_interest, 2),
            'base_tenure': base_tenure,
            'modified_tenure': modified_tenure
        }
