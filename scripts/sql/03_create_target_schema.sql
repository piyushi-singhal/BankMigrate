-- 03_create_target_schema.sql
-- Milestone 3: Create normalized target schema and operational tracking tables in BankMigrate_Target

USE BankMigrate_Target;
GO

-- Drop existing tables in reverse dependency order
IF OBJECT_ID('MigrationAudit', 'U') IS NOT NULL DROP TABLE MigrationAudit;
IF OBJECT_ID('MigrationExceptions', 'U') IS NOT NULL DROP TABLE MigrationExceptions;
IF OBJECT_ID('MigrationRuns', 'U') IS NOT NULL DROP TABLE MigrationRuns;
IF OBJECT_ID('Transactions', 'U') IS NOT NULL DROP TABLE Transactions;
IF OBJECT_ID('Loans', 'U') IS NOT NULL DROP TABLE Loans;
IF OBJECT_ID('Beneficiaries', 'U') IS NOT NULL DROP TABLE Beneficiaries;
IF OBJECT_ID('Accounts', 'U') IS NOT NULL DROP TABLE Accounts;
IF OBJECT_ID('Customers', 'U') IS NOT NULL DROP TABLE Customers;
IF OBJECT_ID('Addresses', 'U') IS NOT NULL DROP TABLE Addresses;
GO

-- 1. Addresses Table
CREATE TABLE Addresses (
    address_id NVARCHAR(50) NOT NULL PRIMARY KEY,
    street_address NVARCHAR(255) NOT NULL,
    city NVARCHAR(100) NOT NULL,
    state NVARCHAR(100) NOT NULL,
    postal_code NVARCHAR(20) NOT NULL,
    country NVARCHAR(100) NOT NULL,
    created_at DATETIME2 DEFAULT SYSDATETIME() NOT NULL
);
GO

-- 2. Customers Table
CREATE TABLE Customers (
    customer_id NVARCHAR(50) NOT NULL PRIMARY KEY,
    full_name NVARCHAR(200) NOT NULL,
    date_of_birth DATE NOT NULL,
    phone_number NVARCHAR(50) NOT NULL,
    email NVARCHAR(200) NOT NULL,
    address_id NVARCHAR(50) NULL FOREIGN KEY REFERENCES Addresses(address_id),
    created_at DATETIME2 DEFAULT SYSDATETIME() NOT NULL
);
GO

-- 3. Accounts Table
CREATE TABLE Accounts (
    account_id NVARCHAR(50) NOT NULL PRIMARY KEY,
    customer_id NVARCHAR(50) NOT NULL FOREIGN KEY REFERENCES Customers(customer_id),
    account_type NVARCHAR(50) NOT NULL, -- SAVINGS, CHECKING, CURRENT, LOAN
    balance DECIMAL(18, 2) NOT NULL,
    opened_date DATE NOT NULL,
    status NVARCHAR(50) NOT NULL, -- ACTIVE, CLOSED, DORMANT
    created_at DATETIME2 DEFAULT SYSDATETIME() NOT NULL
);
GO

-- 4. Transactions Table
CREATE TABLE Transactions (
    transaction_id NVARCHAR(50) NOT NULL PRIMARY KEY,
    account_id NVARCHAR(50) NOT NULL FOREIGN KEY REFERENCES Accounts(account_id),
    transaction_type NVARCHAR(50) NOT NULL, -- DEPOSIT, WITHDRAWAL, TRANSFER
    amount DECIMAL(18, 2) NOT NULL,
    transaction_date DATETIME2 NOT NULL,
    description NVARCHAR(255) NULL,
    created_at DATETIME2 DEFAULT SYSDATETIME() NOT NULL
);
GO

-- 5. Loans Table
CREATE TABLE Loans (
    loan_id NVARCHAR(50) NOT NULL PRIMARY KEY,
    account_id NVARCHAR(50) NOT NULL FOREIGN KEY REFERENCES Accounts(account_id),
    loan_amount DECIMAL(18, 2) NOT NULL,
    interest_rate DECIMAL(5, 2) NOT NULL,
    term_months INT NOT NULL,
    start_date DATE NOT NULL,
    created_at DATETIME2 DEFAULT SYSDATETIME() NOT NULL
);
GO

-- 6. Beneficiaries Table
CREATE TABLE Beneficiaries (
    beneficiary_id NVARCHAR(50) NOT NULL PRIMARY KEY,
    customer_id NVARCHAR(50) NOT NULL FOREIGN KEY REFERENCES Customers(customer_id),
    beneficiary_name NVARCHAR(200) NOT NULL,
    account_number NVARCHAR(50) NOT NULL,
    routing_code NVARCHAR(50) NOT NULL,
    created_at DATETIME2 DEFAULT SYSDATETIME() NOT NULL
);
GO

-- 7. MigrationRuns Table (Run Tracking - Section 15)
CREATE TABLE MigrationRuns (
    run_id NVARCHAR(50) NOT NULL PRIMARY KEY,
    started_at DATETIME2 NOT NULL,
    completed_at DATETIME2 NULL,
    source_records INT DEFAULT 0 NOT NULL,
    validated_records INT DEFAULT 0 NOT NULL,
    transformed_records INT DEFAULT 0 NOT NULL,
    loaded_records INT DEFAULT 0 NOT NULL,
    rejected_records INT DEFAULT 0 NOT NULL,
    status NVARCHAR(50) NOT NULL -- IN_PROGRESS, COMPLETED, COMPLETED_WITH_EXCEPTIONS, FAILED, PARTIAL_FAILURE
);
GO

-- 8. MigrationExceptions Table (Exception Store - Section 13)
CREATE TABLE MigrationExceptions (
    exception_id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    run_id NVARCHAR(50) NOT NULL FOREIGN KEY REFERENCES MigrationRuns(run_id),
    entity_type NVARCHAR(50) NOT NULL, -- Customer / Account / Transaction / Loan / etc.
    record_id NVARCHAR(50) NULL, -- Natural ID of the failing record
    rule_id NVARCHAR(50) NOT NULL, -- Validation rule ID (e.g. TXN_002)
    severity NVARCHAR(20) NOT NULL, -- ERROR / WARNING
    error_message NVARCHAR(MAX) NOT NULL, -- Human-readable explanation
    source_data NVARCHAR(MAX) NULL, -- Snapshot of original record
    created_at DATETIME2 DEFAULT SYSDATETIME() NOT NULL,
    status NVARCHAR(20) DEFAULT 'OPEN' NOT NULL -- OPEN / RESOLVED / IGNORED
);
GO

-- 9. MigrationAudit Table (Audit Logging - Section 16)
CREATE TABLE MigrationAudit (
    audit_id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    run_id NVARCHAR(50) NOT NULL FOREIGN KEY REFERENCES MigrationRuns(run_id),
    entity NVARCHAR(50) NOT NULL, -- Customer / Account / Transaction / etc.
    record_id NVARCHAR(50) NOT NULL, -- Natural ID of affected record
    operation NVARCHAR(50) NOT NULL, -- INSERT / UPDATE / REJECT
    timestamp DATETIME2 DEFAULT SYSDATETIME() NOT NULL,
    status NVARCHAR(50) NOT NULL -- SUCCESS / FAILURE
);
GO
