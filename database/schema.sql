-- Loan Dashboard Database Schema

-- Loans Table
CREATE TABLE IF NOT EXISTS loans (
    loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_name TEXT NOT NULL,
    loan_type TEXT CHECK(loan_type IN ('HOME', 'PERSONAL', 'AUTO')),
    bank_name TEXT,
    principal_amount DECIMAL(12,2),
    sanctioned_amount DECIMAL(12,2),
    interest_rate DECIMAL(5,2),
    rate_type TEXT CHECK(rate_type IN ('FIXED', 'FLOATING')),
    loan_term_months INTEGER,
    start_date DATE,
    emi_amount DECIMAL(10,2),
    payment_frequency TEXT CHECK(payment_frequency IN ('MONTHLY', 'QUARTERLY', 'ANNUALLY')),
    status TEXT CHECK(status IN ('ACTIVE', 'CLOSED', 'PENDING')) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Payments Table
CREATE TABLE IF NOT EXISTS payments (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id INTEGER,
    payment_date DATE,
    scheduled_date DATE,
    principal_component DECIMAL(10,2),
    interest_component DECIMAL(10,2),
    total_amount DECIMAL(10,2),
    payment_type TEXT CHECK(payment_type IN ('EMI', 'PREPAYMENT', 'PARTIAL', 'CHARGES', 'PRE-EMI')),
    payment_method TEXT,
    charges DECIMAL(10,2) DEFAULT 0,
    balance_remaining DECIMAL(12,2),
    status TEXT CHECK(status IN ('PAID', 'PENDING', 'MISSED')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (loan_id) REFERENCES loans(loan_id) ON DELETE CASCADE
);

-- Interest Rate History Table
CREATE TABLE IF NOT EXISTS interest_rate_history (
    rate_id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id INTEGER,
    effective_date DATE,
    interest_rate DECIMAL(5,2),
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (loan_id) REFERENCES loans(loan_id) ON DELETE CASCADE
);

-- Loan Disbursements Table
CREATE TABLE IF NOT EXISTS loan_disbursements (
    disbursement_id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id INTEGER,
    disbursement_date DATE,
    amount DECIMAL(12,2),
    new_emi DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (loan_id) REFERENCES loans(loan_id) ON DELETE CASCADE
);

-- Forecast Scenarios Table
CREATE TABLE IF NOT EXISTS forecast_scenarios (
    scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id INTEGER,
    scenario_name TEXT,
    prepayment_type TEXT CHECK(prepayment_type IN ('LUMPSUM', 'RECURRING_PERCENT')),
    prepayment_value DECIMAL(12,2),
    start_month INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (loan_id) REFERENCES loans(loan_id) ON DELETE CASCADE
);

-- Create Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_payments_loan_id ON payments(loan_id);
CREATE INDEX IF NOT EXISTS idx_payments_date ON payments(payment_date);
CREATE INDEX IF NOT EXISTS idx_rate_history_loan_id ON interest_rate_history(loan_id);
CREATE INDEX IF NOT EXISTS idx_rate_history_date ON interest_rate_history(effective_date);
CREATE INDEX IF NOT EXISTS idx_disbursements_loan_id ON loan_disbursements(loan_id);
CREATE INDEX IF NOT EXISTS idx_scenarios_loan_id ON forecast_scenarios(loan_id);
CREATE INDEX IF NOT EXISTS idx_loans_status ON loans(status);
