"""
Application-wide constants and configuration values.
"""

# Loan Types
LOAN_TYPES = ['HOME', 'PERSONAL', 'AUTO']

# Payment Frequencies
PAYMENT_FREQUENCIES = ['MONTHLY', 'QUARTERLY', 'ANNUALLY']

# Rate Types
RATE_TYPES = ['FIXED', 'FLOATING']

# Payment Methods
PAYMENT_METHODS = ['Auto-debit', 'UPI', 'NEFT', 'IMPS', 'Cheque', 'Cash']

# Payment Types
PAYMENT_TYPES = ['EMI', 'PREPAYMENT', 'PARTIAL', 'CHARGES', 'PRE-EMI']

# Prepayment Types
PREPAYMENT_TYPES = ['LUMPSUM', 'RECURRING_PERCENT']

# Status Options
LOAN_STATUS = ['ACTIVE', 'CLOSED', 'PENDING']
PAYMENT_STATUS = ['PAID', 'PENDING', 'MISSED']

# UI Constants
MAX_FORECAST_SCENARIOS = 5
DEFAULT_CHART_HEIGHT = 400
ITEMS_PER_PAGE = 20

# Calculation Constants
MONTHS_IN_YEAR = 12

# Database
DEFAULT_DB_PATH = 'loan_dashboard.db'
BACKUP_DIR = 'backups'

# Date Format
DATE_FORMAT = '%Y-%m-%d'
DISPLAY_DATE_FORMAT = '%d-%b-%Y'
