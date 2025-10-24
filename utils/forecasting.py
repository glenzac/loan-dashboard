"""
Forecasting module for prepayment scenario simulations.
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dateutil.relativedelta import relativedelta
from utils.calculations import LoanCalculator
from utils.amortization import AmortizationSchedule
from database.models import Loan, Payment, ForecastScenario


class ScenarioForecaster:
    """Create and compare prepayment scenarios."""

    def __init__(self, loan_id: int):
        """
        Initialize forecaster with loan details.

        Args:
            loan_id: ID of the loan to forecast
        """
        self.loan = Loan.get_by_id(loan_id)
        if not self.loan:
            raise ValueError(f"Loan with ID {loan_id} not found")

        self.loan_id = loan_id

        # Get current outstanding balance
        payments = Payment.get_by_loan(loan_id)
        if payments:
            self.current_outstanding = payments[0].balance_remaining
            self.months_elapsed = len([p for p in payments if p.status == 'PAID'])
        else:
            self.current_outstanding = self.loan.principal_amount
            self.months_elapsed = 0

        self.remaining_months = self.loan.loan_term_months - self.months_elapsed

    def create_baseline_scenario(self) -> Dict:
        """
        Create baseline scenario (no prepayments).

        Returns:
            Dictionary with baseline scenario data
        """
        # Generate schedule from current state
        loan_details = {
            'principal': self.current_outstanding,
            'annual_rate': float(self.loan.interest_rate),
            'tenure_months': self.remaining_months,
            'emi': float(self.loan.emi_amount),
            'start_date': datetime.now().strftime('%Y-%m-%d'),
            'payment_frequency': self.loan.payment_frequency
        }

        amortization = AmortizationSchedule(loan_details)
        schedule = amortization.generate_standard_schedule()
        summary = amortization.get_summary_metrics(schedule)

        return {
            'scenario_name': 'Baseline (No Prepayment)',
            'scenario_type': 'BASELINE',
            'schedule': schedule,
            'total_interest': summary['total_interest'],
            'total_amount': summary['total_amount'],
            'tenure_months': summary['actual_tenure'],
            'total_payments': summary['total_payments'],
            'closure_date': self._calculate_closure_date(summary['actual_tenure'])
        }

    def create_lumpsum_scenario(
        self,
        amount: float,
        month: int,
        scenario_name: Optional[str] = None
    ) -> Dict:
        """
        Create scenario with one-time lumpsum prepayment.

        Args:
            amount: Lumpsum prepayment amount
            month: Month number (from now) when prepayment is made
            scenario_name: Optional name for the scenario

        Returns:
            Dictionary with scenario data
        """
        if amount <= 0:
            raise ValueError("Prepayment amount must be positive")

        if month < 1 or month > self.remaining_months:
            raise ValueError(f"Month must be between 1 and {self.remaining_months}")

        # Generate baseline schedule first
        loan_details = {
            'principal': self.current_outstanding,
            'annual_rate': float(self.loan.interest_rate),
            'tenure_months': self.remaining_months,
            'emi': float(self.loan.emi_amount),
            'start_date': datetime.now().strftime('%Y-%m-%d'),
            'payment_frequency': self.loan.payment_frequency
        }

        amortization = AmortizationSchedule(loan_details)

        # Apply prepayment
        prepayments = [{'month': month, 'amount': amount}]
        schedule, summary = amortization.apply_prepayments(prepayments)

        from utils.formatting import format_indian_currency
        name = scenario_name or f"Lumpsum {format_indian_currency(amount, show_decimals=False)} in Month {month}"

        # Calculate savings vs baseline
        baseline = self.create_baseline_scenario()
        interest_saved = baseline['total_interest'] - summary['total_interest']
        months_saved = baseline['tenure_months'] - summary['actual_tenure']

        return {
            'scenario_name': name,
            'scenario_type': 'LUMPSUM',
            'prepayment_amount': amount,
            'prepayment_month': month,
            'schedule': schedule,
            'total_interest': summary['total_interest'],
            'total_amount': summary['total_amount'],
            'tenure_months': summary['actual_tenure'],
            'total_payments': summary['total_payments'],
            'closure_date': self._calculate_closure_date(summary['actual_tenure']),
            'interest_saved': interest_saved,
            'months_saved': months_saved,
            'total_prepayment': amount
        }

    def create_recurring_scenario(
        self,
        percentage_increase: float,
        start_month: int = 1,
        scenario_name: Optional[str] = None
    ) -> Dict:
        """
        Create scenario with recurring EMI increase.

        Args:
            percentage_increase: Percentage increase in EMI
            start_month: Month to start increased EMI
            scenario_name: Optional name for the scenario

        Returns:
            Dictionary with scenario data
        """
        if percentage_increase <= 0 or percentage_increase > 100:
            raise ValueError("Percentage increase must be between 0 and 100")

        # Calculate increased EMI
        base_emi = float(self.loan.emi_amount)
        increased_emi = base_emi * (1 + percentage_increase / 100)

        # Simulate payment schedule with increased EMI
        schedule_data = []
        outstanding = self.current_outstanding
        month_number = 0
        total_interest_paid = 0
        total_principal_paid = 0
        total_prepayment = 0

        annual_rate = float(self.loan.interest_rate)
        start_date = datetime.now()

        while outstanding > 0.01 and month_number < self.remaining_months:
            month_number += 1
            payment_date = start_date + relativedelta(months=month_number)

            # Use increased EMI from start_month onwards
            if month_number >= start_month:
                emi = increased_emi
                extra_payment = increased_emi - base_emi
            else:
                emi = base_emi
                extra_payment = 0

            # Split payment
            principal_component, interest_component = LoanCalculator.split_payment(
                emi,
                outstanding,
                annual_rate
            )

            # Handle final payment
            if principal_component > outstanding:
                principal_component = outstanding
                emi = principal_component + interest_component

            outstanding -= principal_component
            total_interest_paid += interest_component
            total_principal_paid += principal_component
            total_prepayment += extra_payment

            if outstanding < 0.01:
                outstanding = 0

            schedule_data.append({
                'payment_number': month_number,
                'month': month_number,
                'date': payment_date.strftime('%Y-%m-%d'),
                'emi': round(emi, 2),
                'principal': round(principal_component, 2),
                'interest': round(interest_component, 2),
                'balance': round(outstanding, 2),
                'extra_payment': round(extra_payment, 2)
            })

        schedule = pd.DataFrame(schedule_data)

        name = scenario_name or f"Increase EMI by {percentage_increase}% from Month {start_month}"

        # Calculate savings vs baseline
        baseline = self.create_baseline_scenario()
        interest_saved = baseline['total_interest'] - total_interest_paid
        months_saved = baseline['tenure_months'] - month_number

        return {
            'scenario_name': name,
            'scenario_type': 'RECURRING_PERCENT',
            'percentage_increase': percentage_increase,
            'start_month': start_month,
            'increased_emi': increased_emi,
            'schedule': schedule,
            'total_interest': round(total_interest_paid, 2),
            'total_amount': round(total_principal_paid + total_interest_paid, 2),
            'tenure_months': month_number,
            'total_payments': len(schedule),
            'closure_date': self._calculate_closure_date(month_number),
            'interest_saved': interest_saved,
            'months_saved': months_saved,
            'total_prepayment': round(total_prepayment, 2)
        }

    def create_custom_prepayment_scenario(
        self,
        prepayments: List[Dict],
        scenario_name: str
    ) -> Dict:
        """
        Create scenario with multiple custom prepayments.

        Args:
            prepayments: List of {'month': int, 'amount': float}
            scenario_name: Name for the scenario

        Returns:
            Dictionary with scenario data
        """
        loan_details = {
            'principal': self.current_outstanding,
            'annual_rate': float(self.loan.interest_rate),
            'tenure_months': self.remaining_months,
            'emi': float(self.loan.emi_amount),
            'start_date': datetime.now().strftime('%Y-%m-%d'),
            'payment_frequency': self.loan.payment_frequency
        }

        amortization = AmortizationSchedule(loan_details)
        schedule, summary = amortization.apply_prepayments(prepayments)

        # Calculate savings vs baseline
        baseline = self.create_baseline_scenario()
        interest_saved = baseline['total_interest'] - summary['total_interest']
        months_saved = baseline['tenure_months'] - summary['actual_tenure']

        total_prepayment = sum(p['amount'] for p in prepayments)

        return {
            'scenario_name': scenario_name,
            'scenario_type': 'CUSTOM',
            'prepayments': prepayments,
            'schedule': schedule,
            'total_interest': summary['total_interest'],
            'total_amount': summary['total_amount'],
            'tenure_months': summary['actual_tenure'],
            'total_payments': summary['total_payments'],
            'closure_date': self._calculate_closure_date(summary['actual_tenure']),
            'interest_saved': interest_saved,
            'months_saved': months_saved,
            'total_prepayment': total_prepayment
        }

    def compare_scenarios(self, scenarios: List[Dict]) -> pd.DataFrame:
        """
        Compare multiple scenarios.

        Args:
            scenarios: List of scenario dictionaries

        Returns:
            DataFrame with comparison metrics
        """
        comparison_data = []

        for scenario in scenarios:
            comparison_data.append({
                'Scenario': scenario['scenario_name'],
                'Total Interest (₹)': scenario['total_interest'],
                'Total Amount (₹)': scenario['total_amount'],
                'Tenure (Months)': scenario['tenure_months'],
                'Closure Date': scenario['closure_date'],
                'Interest Saved (₹)': scenario.get('interest_saved', 0),
                'Months Saved': scenario.get('months_saved', 0),
                'Total Prepayment (₹)': scenario.get('total_prepayment', 0)
            })

        return pd.DataFrame(comparison_data)

    def calculate_savings(self, scenario: Dict) -> Dict:
        """
        Calculate detailed savings for a scenario.

        Args:
            scenario: Scenario dictionary

        Returns:
            Dictionary with savings details
        """
        baseline = self.create_baseline_scenario()

        interest_saved = baseline['total_interest'] - scenario['total_interest']
        months_saved = baseline['tenure_months'] - scenario['tenure_months']
        prepayment_cost = scenario.get('total_prepayment', 0)

        # Net benefit = interest saved - opportunity cost (simplified)
        net_benefit = interest_saved - (prepayment_cost * 0.05)  # Assuming 5% opportunity cost

        return {
            'baseline_interest': baseline['total_interest'],
            'scenario_interest': scenario['total_interest'],
            'interest_saved': interest_saved,
            'interest_saved_percent': (interest_saved / baseline['total_interest'] * 100)
                if baseline['total_interest'] > 0 else 0,
            'baseline_tenure': baseline['tenure_months'],
            'scenario_tenure': scenario['tenure_months'],
            'months_saved': months_saved,
            'months_saved_percent': (months_saved / baseline['tenure_months'] * 100)
                if baseline['tenure_months'] > 0 else 0,
            'prepayment_amount': prepayment_cost,
            'net_benefit': net_benefit,
            'baseline_closure': baseline['closure_date'],
            'scenario_closure': scenario['closure_date']
        }

    def save_scenario(self, scenario: Dict) -> int:
        """
        Save scenario to database.

        Args:
            scenario: Scenario dictionary

        Returns:
            Scenario ID
        """
        scenario_data = {
            'loan_id': self.loan_id,
            'scenario_name': scenario['scenario_name'],
            'prepayment_type': scenario['scenario_type'],
            'prepayment_value': scenario.get('prepayment_amount', 0) or
                               scenario.get('percentage_increase', 0),
            'start_month': scenario.get('prepayment_month', 0) or
                          scenario.get('start_month', 0)
        }

        return ForecastScenario.create(scenario_data)

    def load_saved_scenarios(self) -> List[Dict]:
        """
        Load saved scenarios from database.

        Returns:
            List of scenario dictionaries
        """
        saved_scenarios = ForecastScenario.get_by_loan(self.loan_id)
        scenarios = []

        for saved in saved_scenarios:
            if saved.prepayment_type == 'LUMPSUM':
                scenario = self.create_lumpsum_scenario(
                    amount=saved.prepayment_value,
                    month=saved.start_month,
                    scenario_name=saved.scenario_name
                )
            elif saved.prepayment_type == 'RECURRING_PERCENT':
                scenario = self.create_recurring_scenario(
                    percentage_increase=saved.prepayment_value,
                    start_month=saved.start_month,
                    scenario_name=saved.scenario_name
                )
            else:
                continue

            scenario['scenario_id'] = saved.scenario_id
            scenarios.append(scenario)

        return scenarios

    def _calculate_closure_date(self, months_from_now: int) -> str:
        """
        Calculate loan closure date.

        Args:
            months_from_now: Number of months from now

        Returns:
            Closure date as string
        """
        closure_date = datetime.now() + relativedelta(months=int(months_from_now))
        return closure_date.strftime('%Y-%m-%d')

    def get_optimal_prepayment_analysis(
        self,
        available_amount: float,
        analysis_months: int = 12
    ) -> List[Dict]:
        """
        Analyze optimal prepayment timing.

        Args:
            available_amount: Amount available for prepayment
            analysis_months: Number of months to analyze

        Returns:
            List of scenarios for different prepayment months
        """
        scenarios = []

        for month in range(1, min(analysis_months + 1, self.remaining_months + 1)):
            try:
                scenario = self.create_lumpsum_scenario(
                    amount=available_amount,
                    month=month,
                    scenario_name=f"Prepay in Month {month}"
                )
                scenarios.append(scenario)
            except:
                continue

        return scenarios

    def calculate_breakeven_prepayment(
        self,
        target_months_saved: int
    ) -> Optional[float]:
        """
        Calculate prepayment amount needed to save target months.

        Args:
            target_months_saved: Target number of months to save

        Returns:
            Required prepayment amount or None
        """
        # Binary search for the right prepayment amount
        low, high = 1000, self.current_outstanding
        tolerance = 100  # ₹100 tolerance

        best_amount = None

        while low <= high:
            mid = (low + high) / 2

            try:
                scenario = self.create_lumpsum_scenario(amount=mid, month=1)
                months_saved = scenario.get('months_saved', 0)

                if abs(months_saved - target_months_saved) <= 1:
                    best_amount = mid
                    break
                elif months_saved < target_months_saved:
                    low = mid + tolerance
                else:
                    high = mid - tolerance
                    best_amount = mid

            except:
                break

            if high - low < tolerance:
                break

        return round(best_amount, 2) if best_amount else None
