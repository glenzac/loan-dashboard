"""
Comprehensive input validation utilities for loan dashboard.

This module provides validators for all user inputs to ensure data integrity
and prevent invalid data from entering the database.
"""

from typing import Dict, List, Optional, Tuple
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import re


class ValidationError(Exception):
    """Custom exception for validation errors."""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


class ValidationResult:
    """Result of a validation operation."""

    def __init__(self):
        self.is_valid = True
        self.errors: List[Tuple[str, str]] = []  # List of (field, message) tuples

    def add_error(self, field: str, message: str):
        """Add a validation error."""
        self.is_valid = False
        self.errors.append((field, message))

    def get_errors(self) -> List[str]:
        """Get formatted error messages."""
        return [f"❌ {field}: {message}" for field, message in self.errors]

    def get_error_dict(self) -> Dict[str, List[str]]:
        """Get errors grouped by field."""
        error_dict = {}
        for field, message in self.errors:
            if field not in error_dict:
                error_dict[field] = []
            error_dict[field].append(message)
        return error_dict


class LoanValidator:
    """Validator for loan-related inputs."""

    # Constants for validation
    MIN_LOAN_NAME_LENGTH = 3
    MAX_LOAN_NAME_LENGTH = 100
    MIN_PRINCIPAL = 1000.0  # Minimum ₹1,000
    MAX_PRINCIPAL = 100000000.0  # Maximum ₹10 Crore
    MIN_INTEREST_RATE = 0.01  # 0.01%
    MAX_INTEREST_RATE = 50.0  # 50%
    MIN_TENURE_MONTHS = 1
    MAX_TENURE_MONTHS = 360  # 30 years
    MIN_EMI = 100.0

    # Valid loan types
    VALID_LOAN_TYPES = ['HOME', 'PERSONAL', 'AUTO', 'EDUCATION', 'GOLD', 'OTHER']
    VALID_RATE_TYPES = ['FIXED', 'FLOATING']
    VALID_PAYMENT_FREQUENCIES = ['MONTHLY', 'QUARTERLY', 'ANNUALLY']
    VALID_LOAN_STATUSES = ['ACTIVE', 'CLOSED', 'PENDING']

    @staticmethod
    def validate_loan_name(loan_name: str) -> ValidationResult:
        """
        Validate loan name.

        Rules:
        - Required (not empty)
        - Length between 3 and 100 characters
        - No leading/trailing whitespace
        - No special characters except: -_()&.
        """
        result = ValidationResult()

        if not loan_name or not loan_name.strip():
            result.add_error("Loan Name", "Loan name is required")
            return result

        loan_name = loan_name.strip()

        if len(loan_name) < LoanValidator.MIN_LOAN_NAME_LENGTH:
            result.add_error("Loan Name",
                f"Loan name must be at least {LoanValidator.MIN_LOAN_NAME_LENGTH} characters")

        if len(loan_name) > LoanValidator.MAX_LOAN_NAME_LENGTH:
            result.add_error("Loan Name",
                f"Loan name must not exceed {LoanValidator.MAX_LOAN_NAME_LENGTH} characters")

        # Check for valid characters (alphanumeric, spaces, and specific special chars)
        if not re.match(r'^[a-zA-Z0-9\s\-_()&.]+$', loan_name):
            result.add_error("Loan Name",
                "Loan name can only contain letters, numbers, spaces, and: - _ ( ) & .")

        return result

    @staticmethod
    def validate_bank_name(bank_name: str) -> ValidationResult:
        """
        Validate bank name.

        Rules:
        - Required (not empty)
        - Length between 2 and 100 characters
        """
        result = ValidationResult()

        if not bank_name or not bank_name.strip():
            result.add_error("Bank Name", "Bank name is required")
            return result

        bank_name = bank_name.strip()

        if len(bank_name) < 2:
            result.add_error("Bank Name", "Bank name must be at least 2 characters")

        if len(bank_name) > 100:
            result.add_error("Bank Name", "Bank name must not exceed 100 characters")

        return result

    @staticmethod
    def validate_amount(amount: float, field_name: str,
                       min_value: float = MIN_PRINCIPAL,
                       max_value: float = MAX_PRINCIPAL,
                       allow_zero: bool = False) -> ValidationResult:
        """
        Validate monetary amount.

        Args:
            amount: Amount to validate
            field_name: Name of the field for error messages
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            allow_zero: Whether zero is allowed
        """
        result = ValidationResult()

        try:
            amount = float(amount)
        except (ValueError, TypeError):
            result.add_error(field_name, "Must be a valid number")
            return result

        if not allow_zero and amount <= 0:
            result.add_error(field_name, "Must be greater than zero")
        elif allow_zero and amount < 0:
            result.add_error(field_name, "Cannot be negative")

        if amount < min_value:
            result.add_error(field_name,
                f"Must be at least ₹{min_value:,.2f}")

        if amount > max_value:
            result.add_error(field_name,
                f"Must not exceed ₹{max_value:,.2f}")

        # Check for reasonable decimal places (max 2)
        if round(amount, 2) != amount:
            result.add_error(field_name,
                "Maximum 2 decimal places allowed")

        return result

    @staticmethod
    def validate_interest_rate(rate: float) -> ValidationResult:
        """
        Validate interest rate.

        Rules:
        - Between 0.01% and 50%
        - Maximum 2 decimal places
        """
        result = ValidationResult()

        try:
            rate = float(rate)
        except (ValueError, TypeError):
            result.add_error("Interest Rate", "Must be a valid number")
            return result

        if rate < LoanValidator.MIN_INTEREST_RATE:
            result.add_error("Interest Rate",
                f"Must be at least {LoanValidator.MIN_INTEREST_RATE}%")

        if rate > LoanValidator.MAX_INTEREST_RATE:
            result.add_error("Interest Rate",
                f"Must not exceed {LoanValidator.MAX_INTEREST_RATE}%")

        # Check for reasonable decimal places (max 2)
        if round(rate, 2) != rate:
            result.add_error("Interest Rate",
                "Maximum 2 decimal places allowed")

        return result

    @staticmethod
    def validate_tenure(months: int) -> ValidationResult:
        """
        Validate loan tenure in months.

        Rules:
        - Integer value
        - Between 1 and 360 months (30 years)
        """
        result = ValidationResult()

        try:
            months = int(months)
        except (ValueError, TypeError):
            result.add_error("Loan Tenure", "Must be a valid number")
            return result

        if months < LoanValidator.MIN_TENURE_MONTHS:
            result.add_error("Loan Tenure",
                f"Must be at least {LoanValidator.MIN_TENURE_MONTHS} month")

        if months > LoanValidator.MAX_TENURE_MONTHS:
            result.add_error("Loan Tenure",
                f"Must not exceed {LoanValidator.MAX_TENURE_MONTHS} months (30 years)")

        return result

    @staticmethod
    def validate_date(date_value: date, field_name: str,
                     allow_future: bool = False,
                     allow_past: bool = True,
                     min_date: Optional[date] = None,
                     max_date: Optional[date] = None) -> ValidationResult:
        """
        Validate date.

        Args:
            date_value: Date to validate
            field_name: Name of the field for error messages
            allow_future: Whether future dates are allowed
            allow_past: Whether past dates are allowed
            min_date: Minimum allowed date
            max_date: Maximum allowed date
        """
        result = ValidationResult()

        if not isinstance(date_value, date):
            result.add_error(field_name, "Must be a valid date")
            return result

        today = date.today()

        if not allow_future and date_value > today:
            result.add_error(field_name, "Future dates are not allowed")

        if not allow_past and date_value < today:
            result.add_error(field_name, "Past dates are not allowed")

        if min_date and date_value < min_date:
            result.add_error(field_name,
                f"Must be on or after {min_date.strftime('%d-%m-%Y')}")

        if max_date and date_value > max_date:
            result.add_error(field_name,
                f"Must be on or before {max_date.strftime('%d-%m-%Y')}")

        return result

    @staticmethod
    def validate_loan_type(loan_type: str) -> ValidationResult:
        """Validate loan type."""
        result = ValidationResult()

        if loan_type not in LoanValidator.VALID_LOAN_TYPES:
            result.add_error("Loan Type",
                f"Must be one of: {', '.join(LoanValidator.VALID_LOAN_TYPES)}")

        return result

    @staticmethod
    def validate_rate_type(rate_type: str) -> ValidationResult:
        """Validate rate type (FIXED/FLOATING)."""
        result = ValidationResult()

        if rate_type not in LoanValidator.VALID_RATE_TYPES:
            result.add_error("Rate Type",
                f"Must be one of: {', '.join(LoanValidator.VALID_RATE_TYPES)}")

        return result

    @staticmethod
    def validate_payment_frequency(frequency: str) -> ValidationResult:
        """Validate payment frequency."""
        result = ValidationResult()

        if frequency not in LoanValidator.VALID_PAYMENT_FREQUENCIES:
            result.add_error("Payment Frequency",
                f"Must be one of: {', '.join(LoanValidator.VALID_PAYMENT_FREQUENCIES)}")

        return result

    @staticmethod
    def validate_complete_loan(loan_data: Dict) -> ValidationResult:
        """
        Validate complete loan data.

        Performs all validations and checks relationships between fields.
        """
        result = ValidationResult()

        # Validate individual fields
        name_result = LoanValidator.validate_loan_name(loan_data.get('loan_name', ''))
        if not name_result.is_valid:
            result.errors.extend(name_result.errors)

        bank_result = LoanValidator.validate_bank_name(loan_data.get('bank_name', ''))
        if not bank_result.is_valid:
            result.errors.extend(bank_result.errors)

        principal_result = LoanValidator.validate_amount(
            loan_data.get('principal_amount', 0),
            "Principal Amount"
        )
        if not principal_result.is_valid:
            result.errors.extend(principal_result.errors)

        sanctioned_result = LoanValidator.validate_amount(
            loan_data.get('sanctioned_amount', 0),
            "Sanctioned Amount"
        )
        if not sanctioned_result.is_valid:
            result.errors.extend(sanctioned_result.errors)

        rate_result = LoanValidator.validate_interest_rate(
            loan_data.get('interest_rate', 0)
        )
        if not rate_result.is_valid:
            result.errors.extend(rate_result.errors)

        tenure_result = LoanValidator.validate_tenure(
            loan_data.get('loan_term_months', 0)
        )
        if not tenure_result.is_valid:
            result.errors.extend(tenure_result.errors)

        emi_result = LoanValidator.validate_amount(
            loan_data.get('emi_amount', 0),
            "EMI Amount",
            min_value=LoanValidator.MIN_EMI,
            max_value=LoanValidator.MAX_PRINCIPAL
        )
        if not emi_result.is_valid:
            result.errors.extend(emi_result.errors)

        # Validate date
        start_date_str = loan_data.get('start_date')
        if start_date_str:
            try:
                if isinstance(start_date_str, str):
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                else:
                    start_date = start_date_str

                date_result = LoanValidator.validate_date(
                    start_date,
                    "Start Date",
                    allow_future=True,
                    allow_past=True
                )
                if not date_result.is_valid:
                    result.errors.extend(date_result.errors)
            except ValueError:
                result.add_error("Start Date", "Invalid date format (expected YYYY-MM-DD)")

        # Validate categorical fields
        loan_type_result = LoanValidator.validate_loan_type(
            loan_data.get('loan_type', '')
        )
        if not loan_type_result.is_valid:
            result.errors.extend(loan_type_result.errors)

        rate_type_result = LoanValidator.validate_rate_type(
            loan_data.get('rate_type', '')
        )
        if not rate_type_result.is_valid:
            result.errors.extend(rate_type_result.errors)

        frequency_result = LoanValidator.validate_payment_frequency(
            loan_data.get('payment_frequency', '')
        )
        if not frequency_result.is_valid:
            result.errors.extend(frequency_result.errors)

        # Cross-field validation
        principal = loan_data.get('principal_amount', 0)
        sanctioned = loan_data.get('sanctioned_amount', 0)

        if principal > sanctioned:
            result.add_error("Principal Amount",
                "Cannot exceed sanctioned amount")

        # Validate EMI is reasonable for principal and tenure
        if principal > 0 and loan_data.get('loan_term_months', 0) > 0:
            emi = loan_data.get('emi_amount', 0)
            # EMI should be at least principal/tenure (interest-free case)
            min_expected_emi = principal / loan_data['loan_term_months']
            # EMI should not exceed principal itself (unreasonable)
            if emi < min_expected_emi * 0.5:
                result.add_error("EMI Amount",
                    f"EMI seems too low for principal ₹{principal:,.2f} over {loan_data['loan_term_months']} months. Expected minimum around ₹{min_expected_emi:,.2f}")
            if emi > principal:
                result.add_error("EMI Amount",
                    "EMI cannot exceed the principal amount")

        if not result.errors:
            result.is_valid = True
        else:
            result.is_valid = False

        return result


class PaymentValidator:
    """Validator for payment-related inputs."""

    # Valid payment types and methods
    VALID_PAYMENT_TYPES = ['EMI', 'PREPAYMENT', 'PRE-EMI', 'CHARGES', 'PARTIAL']
    VALID_PAYMENT_STATUS = ['PAID', 'PENDING', 'MISSED', 'CANCELLED']

    MIN_PAYMENT = 1.0
    MAX_PAYMENT = 10000000.0  # ₹1 Crore max per payment

    @staticmethod
    def validate_payment_amount(amount: float, field_name: str = "Payment Amount") -> ValidationResult:
        """Validate payment amount."""
        return LoanValidator.validate_amount(
            amount,
            field_name,
            min_value=PaymentValidator.MIN_PAYMENT,
            max_value=PaymentValidator.MAX_PAYMENT
        )

    @staticmethod
    def validate_payment_breakdown(total: float, principal: float,
                                   interest: float, payment_type: str) -> ValidationResult:
        """
        Validate payment breakdown components.

        Rules:
        - For EMI/PARTIAL: principal + interest must equal total
        - For PREPAYMENT: interest should be 0
        - For PRE-EMI: principal should be 0
        - For CHARGES: both should be 0
        """
        result = ValidationResult()

        # Validate individual components
        if principal < 0:
            result.add_error("Principal Component", "Cannot be negative")

        if interest < 0:
            result.add_error("Interest Component", "Cannot be negative")

        # Payment type specific validation
        if payment_type in ['EMI', 'PARTIAL']:
            breakdown_total = principal + interest
            # Allow 2 paisa (0.02) difference for rounding
            if abs(breakdown_total - total) > 0.02:
                result.add_error("Payment Breakdown",
                    f"Principal (₹{principal:,.2f}) + Interest (₹{interest:,.2f}) must equal Total Amount (₹{total:,.2f})")

        elif payment_type == 'PREPAYMENT':
            if interest > 0:
                result.add_error("Interest Component",
                    "Should be 0 for prepayment (only principal)")
            if principal != total:
                result.add_error("Principal Component",
                    "Should equal total amount for prepayment")

        elif payment_type == 'PRE-EMI':
            if principal > 0:
                result.add_error("Principal Component",
                    "Should be 0 for PRE-EMI (only interest)")
            if interest != total:
                result.add_error("Interest Component",
                    "Should equal total amount for PRE-EMI")

        elif payment_type == 'CHARGES':
            if principal > 0 or interest > 0:
                result.add_error("Payment Components",
                    "Principal and interest should be 0 for charges")

        return result

    @staticmethod
    def validate_payment_date(payment_date: date, loan_start_date: Optional[date] = None) -> ValidationResult:
        """
        Validate payment date.

        Rules:
        - Cannot be in the future
        - Should not be before loan start date
        """
        result = ValidationResult()

        date_result = LoanValidator.validate_date(
            payment_date,
            "Payment Date",
            allow_future=False,
            allow_past=True
        )

        if not date_result.is_valid:
            result.errors.extend(date_result.errors)

        if loan_start_date and payment_date < loan_start_date:
            result.add_error("Payment Date",
                f"Cannot be before loan start date ({loan_start_date.strftime('%d-%m-%Y')})")

        return result

    @staticmethod
    def validate_complete_payment(payment_data: Dict, loan_data: Optional[Dict] = None) -> ValidationResult:
        """
        Validate complete payment data.

        Args:
            payment_data: Payment data dictionary
            loan_data: Optional loan data for cross-validation
        """
        result = ValidationResult()

        # Validate amount
        total = payment_data.get('total_amount', 0)
        amount_result = PaymentValidator.validate_payment_amount(total)
        if not amount_result.is_valid:
            result.errors.extend(amount_result.errors)

        # Validate breakdown
        principal = payment_data.get('principal_component', 0)
        interest = payment_data.get('interest_component', 0)
        payment_type = payment_data.get('payment_type', 'EMI')

        breakdown_result = PaymentValidator.validate_payment_breakdown(
            total, principal, interest, payment_type
        )
        if not breakdown_result.is_valid:
            result.errors.extend(breakdown_result.errors)

        # Validate date
        payment_date_str = payment_data.get('payment_date')
        if payment_date_str:
            try:
                if isinstance(payment_date_str, str):
                    payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d').date()
                else:
                    payment_date = payment_date_str

                loan_start_date = None
                if loan_data and loan_data.get('start_date'):
                    start_date_str = loan_data['start_date']
                    if isinstance(start_date_str, str):
                        loan_start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                    else:
                        loan_start_date = start_date_str

                date_result = PaymentValidator.validate_payment_date(
                    payment_date,
                    loan_start_date
                )
                if not date_result.is_valid:
                    result.errors.extend(date_result.errors)
            except ValueError:
                result.add_error("Payment Date", "Invalid date format (expected YYYY-MM-DD)")

        # Validate payment type
        if payment_type not in PaymentValidator.VALID_PAYMENT_TYPES:
            result.add_error("Payment Type",
                f"Must be one of: {', '.join(PaymentValidator.VALID_PAYMENT_TYPES)}")

        # Validate status
        status = payment_data.get('status', 'PAID')
        if status not in PaymentValidator.VALID_PAYMENT_STATUS:
            result.add_error("Payment Status",
                f"Must be one of: {', '.join(PaymentValidator.VALID_PAYMENT_STATUS)}")

        # Validate balance
        balance = payment_data.get('balance_remaining', 0)
        if balance < 0:
            result.add_error("Balance Remaining", "Cannot be negative")

        # Cross-validation with loan data
        if loan_data:
            # Check if payment amount is reasonable for loan
            emi_amount = loan_data.get('emi_amount', 0)
            if payment_type == 'EMI' and emi_amount > 0:
                # Allow 10% variance for EMI
                if total < emi_amount * 0.9 or total > emi_amount * 1.1:
                    result.add_error("Payment Amount",
                        f"EMI payment (₹{total:,.2f}) differs significantly from expected EMI (₹{emi_amount:,.2f}). Use 'PARTIAL' payment type if intentional.")

        if not result.errors:
            result.is_valid = True
        else:
            result.is_valid = False

        return result


class DisbursementValidator:
    """Validator for loan disbursement inputs."""

    @staticmethod
    def validate_disbursement(disbursement_amount: float,
                             principal_amount: float,
                             sanctioned_amount: float,
                             disbursement_date: date,
                             loan_start_date: date) -> ValidationResult:
        """
        Validate loan disbursement.

        Rules:
        - Disbursement amount must be positive
        - Cannot exceed remaining sanctioned amount
        - Disbursement date should be after loan start date
        """
        result = ValidationResult()

        # Validate amount
        amount_result = LoanValidator.validate_amount(
            disbursement_amount,
            "Disbursement Amount",
            min_value=1000.0,
            max_value=sanctioned_amount
        )
        if not amount_result.is_valid:
            result.errors.extend(amount_result.errors)

        # Check if disbursement exceeds remaining sanctioned amount
        remaining = sanctioned_amount - principal_amount
        if disbursement_amount > remaining:
            result.add_error("Disbursement Amount",
                f"Cannot exceed remaining sanctioned amount of ₹{remaining:,.2f}")

        # Validate date
        date_result = LoanValidator.validate_date(
            disbursement_date,
            "Disbursement Date",
            allow_future=False,
            allow_past=True,
            min_date=loan_start_date
        )
        if not date_result.is_valid:
            result.errors.extend(date_result.errors)

        if not result.errors:
            result.is_valid = True
        else:
            result.is_valid = False

        return result


class RateChangeValidator:
    """Validator for interest rate change inputs."""

    @staticmethod
    def validate_rate_change(new_rate: float,
                            current_rate: float,
                            change_date: date,
                            loan_start_date: date) -> ValidationResult:
        """
        Validate interest rate change.

        Rules:
        - New rate must be valid
        - Should be different from current rate
        - Change date should be after loan start date
        """
        result = ValidationResult()

        # Validate new rate
        rate_result = LoanValidator.validate_interest_rate(new_rate)
        if not rate_result.is_valid:
            result.errors.extend(rate_result.errors)

        # Check if rate is actually changing
        if abs(new_rate - current_rate) < 0.01:
            result.add_error("New Interest Rate",
                f"New rate ({new_rate}%) is the same as current rate ({current_rate}%)")

        # Validate date
        date_result = LoanValidator.validate_date(
            change_date,
            "Rate Change Date",
            allow_future=False,
            allow_past=True,
            min_date=loan_start_date
        )
        if not date_result.is_valid:
            result.errors.extend(date_result.errors)

        if not result.errors:
            result.is_valid = True
        else:
            result.is_valid = False

        return result
