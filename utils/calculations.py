"""
Loan calculation utilities using reducing balance method.
"""

from typing import Tuple, Dict
from config.constants import MONTHS_IN_YEAR


class LoanCalculator:
    """Static methods for loan-related financial calculations."""

    @staticmethod
    def calculate_emi(principal: float, annual_rate: float, tenure_months: int) -> float:
        """
        Calculate EMI using reducing balance formula.

        Formula: EMI = P × r × (1+r)^n / ((1+r)^n - 1)
        Where:
            P = Principal loan amount
            r = Monthly interest rate (annual rate / 12 / 100)
            n = Tenure in months

        Args:
            principal: Loan principal amount
            annual_rate: Annual interest rate (percentage)
            tenure_months: Loan tenure in months

        Returns:
            EMI amount (rounded to 2 decimals)
        """
        if principal <= 0 or tenure_months <= 0:
            return 0.0

        if annual_rate == 0:
            return round(principal / tenure_months, 2)

        # Convert annual rate to monthly rate
        monthly_rate = annual_rate / (MONTHS_IN_YEAR * 100)

        # Calculate EMI using formula
        emi = principal * monthly_rate * (
            pow(1 + monthly_rate, tenure_months)
        ) / (pow(1 + monthly_rate, tenure_months) - 1)

        # Round to nearest rupee (no decimals)
        return round(emi, 0)

    @staticmethod
    def split_payment(
        emi_amount: float,
        outstanding_principal: float,
        annual_rate: float
    ) -> Tuple[float, float]:
        """
        Split EMI into principal and interest components.

        Args:
            emi_amount: EMI payment amount
            outstanding_principal: Current outstanding principal
            annual_rate: Annual interest rate (percentage)

        Returns:
            Tuple of (principal_component, interest_component)
        """
        if outstanding_principal <= 0:
            # If no outstanding balance, all payment goes to principal
            return (emi_amount, 0.0)

        # Calculate interest component for the month
        monthly_rate = annual_rate / (MONTHS_IN_YEAR * 100)
        interest_component = outstanding_principal * monthly_rate

        # Principal component is the remainder
        principal_component = emi_amount - interest_component

        # Ensure principal doesn't exceed outstanding
        if principal_component > outstanding_principal:
            principal_component = outstanding_principal

        return (round(principal_component, 2), round(interest_component, 2))

    @staticmethod
    def calculate_prepayment_impact(
        outstanding: float,
        prepayment: float,
        annual_rate: float,
        remaining_months: int,
        current_emi: float
    ) -> Dict[str, any]:
        """
        Calculate impact of prepayment on loan tenure and interest.

        Args:
            outstanding: Outstanding principal before prepayment
            prepayment: Prepayment amount
            annual_rate: Annual interest rate (percentage)
            remaining_months: Remaining tenure in months
            current_emi: Current EMI amount

        Returns:
            Dictionary containing:
                - new_balance: Principal after prepayment (same as new_principal)
                - new_tenure: New tenure in months
                - months_saved: Months saved due to prepayment
                - interest_saved: Interest amount saved
                - new_emi: EMI amount (if keeping same tenure)
        """
        if prepayment >= outstanding:
            return {
                'new_balance': 0.0,
                'new_tenure': 0,
                'months_saved': remaining_months,
                'interest_saved': 0.0,
                'new_emi': 0.0
            }

        new_principal = outstanding - prepayment

        # Calculate original total interest
        original_total = current_emi * remaining_months
        original_interest = original_total - outstanding

        # Calculate new tenure with same EMI
        if annual_rate == 0:
            new_tenure = int(new_principal / current_emi) + (1 if new_principal % current_emi > 0 else 0)
        else:
            monthly_rate = annual_rate / (MONTHS_IN_YEAR * 100)

            # Calculate new tenure: n = log(EMI / (EMI - P*r)) / log(1 + r)
            if current_emi <= new_principal * monthly_rate:
                # EMI too small to cover interest
                new_tenure = remaining_months
            else:
                import math
                new_tenure = math.log(
                    current_emi / (current_emi - new_principal * monthly_rate)
                ) / math.log(1 + monthly_rate)
                new_tenure = int(math.ceil(new_tenure))

        months_saved = remaining_months - new_tenure

        # Calculate new total interest
        new_total = current_emi * new_tenure
        new_interest = new_total - new_principal
        interest_saved = original_interest - new_interest

        # Calculate new EMI if keeping same tenure
        new_emi = LoanCalculator.calculate_emi(
            new_principal,
            annual_rate,
            remaining_months
        )

        return {
            'new_balance': round(new_principal, 2),
            'new_tenure': new_tenure,
            'months_saved': months_saved,
            'interest_saved': round(interest_saved, 2),
            'new_emi': new_emi
        }

    @staticmethod
    def adjust_emi_for_disbursement(
        current_emi: float,
        current_principal: float,
        new_disbursement: float,
        annual_rate: float,
        remaining_months: int
    ) -> float:
        """
        Recalculate EMI after partial disbursement.

        Args:
            current_emi: Current EMI amount
            current_principal: Current outstanding principal
            new_disbursement: New disbursement amount
            annual_rate: Annual interest rate (percentage)
            remaining_months: Remaining tenure in months

        Returns:
            New EMI amount
        """
        new_principal = current_principal + new_disbursement

        return LoanCalculator.calculate_emi(
            new_principal,
            annual_rate,
            remaining_months
        )

    @staticmethod
    def calculate_total_interest(
        principal: float,
        emi: float,
        tenure_months: int
    ) -> float:
        """
        Calculate total interest payable over loan tenure.

        Args:
            principal: Loan principal
            emi: EMI amount
            tenure_months: Tenure in months

        Returns:
            Total interest amount
        """
        total_payment = emi * tenure_months
        total_interest = total_payment - principal
        return round(total_interest, 2)

    @staticmethod
    def calculate_outstanding_principal(
        original_principal: float,
        annual_rate: float,
        emi: float,
        months_elapsed: int
    ) -> float:
        """
        Calculate outstanding principal after given months.

        Args:
            original_principal: Original loan amount
            annual_rate: Annual interest rate (percentage)
            emi: EMI amount
            months_elapsed: Number of months elapsed

        Returns:
            Outstanding principal amount
        """
        if months_elapsed == 0:
            return original_principal

        monthly_rate = annual_rate / (MONTHS_IN_YEAR * 100)
        outstanding = original_principal

        for month in range(months_elapsed):
            interest = outstanding * monthly_rate
            principal_paid = emi - interest
            outstanding -= principal_paid

            if outstanding <= 0:
                return 0.0

        return round(outstanding, 2)

    @staticmethod
    def get_payment_frequency_multiplier(frequency: str) -> int:
        """
        Get multiplier for payment frequency.

        Args:
            frequency: Payment frequency (MONTHLY, QUARTERLY, ANNUALLY)

        Returns:
            Number of months between payments
        """
        frequency_map = {
            'MONTHLY': 1,
            'QUARTERLY': 3,
            'ANNUALLY': 12
        }
        return frequency_map.get(frequency, 1)
