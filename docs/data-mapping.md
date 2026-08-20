# Data Mapping & Entity-Relationship Specifications

## Overview
This document specifies the legacy database schema, target normalized schema, and the transformation rules mapping legacy fields to clean target entities.

---

## Legacy Database Schema (`BankMigrate_Legacy`)

The legacy schema consists of 6 tables. Relationships are not strictly enforced in the engine to simulate dirty legacy data containing orphaned records and invalid foreign keys.

```mermaid
erDiagram
    Customers_Legacy ||--o{ Accounts_Legacy : "has (soft FK customer_id)"
    Customers_Legacy }|--|| Addresses_Legacy : "references (soft FK address_id)"
    Accounts_Legacy ||--o{ Transactions_Legacy : "has (soft FK account_id - Note: contains invalid references like A999999)"
    Accounts_Legacy ||--o{ Loans_Legacy : "has (soft FK account_id)"
    Customers_Legacy ||--o{ Beneficiaries_Legacy : "has (soft FK customer_id)"

    Customers_Legacy {
        string customer_id PK "Primary key; some rows deliberately NULL"
        string customer_name "Free-text, inconsistent casing/spacing"
        string dob "Free-text date, inconsistent formats"
        string phone "Inconsistent formats (+91-, spaces, no country code)"
        string email "Inconsistent casing, stray whitespace"
        string address_id FK "Foreign key to Addresses_Legacy"
    }

    Accounts_Legacy {
        string account_id PK "Primary key"
        string customer_id FK "Foreign key to Customers_Legacy (some invalid)"
        string account_type "e.g. SAVINGS, CURRENT, LOAN"
        decimal balance "Some invalid/negative values"
        string opened_date "Inconsistent date formats"
        string status "ACTIVE, CLOSED, DORMANT"
    }

    Transactions_Legacy {
        string transaction_id PK "Primary key"
        string account_id FK "Foreign key to Accounts_Legacy (some orphaned)"
        string transaction_type "DEPOSIT, WITHDRAWAL, TRANSFER"
        decimal amount "Transaction amount"
        string transaction_date "Inconsistent date formats"
        string description "Free-text transaction note"
    }

    Loans_Legacy {
        string loan_id PK "Primary key"
        string account_id FK "Foreign key to Accounts_Legacy"
        decimal loan_amount "Principal amount"
        decimal interest_rate "Annual percentage rate"
        int term_months "Duration in months"
        string start_date "Inconsistent date formats"
    }

    Beneficiaries_Legacy {
        string beneficiary_id PK "Primary key"
        string customer_id FK "Foreign key to Customers_Legacy"
        string beneficiary_name "Name of beneficiary"
        string account_number "Destination account number"
        string routing_code "Bank routing/IFSC code"
    }

    Addresses_Legacy {
        string address_id PK "Primary key"
        string street_address "Street address line"
        string city "City name"
        string state "State/province"
        string postal_code "Postal code"
        string country "Country name"
    }
```

> [!NOTE]  
> In `BankMigrate_Legacy`, foreign key constraints are omitted or non-enforcing at the database level to permit seeding dirty data (e.g., transactions referencing nonexistent account IDs like `A999999`).

---

## Target Database Schema (`BankMigrate_Target`)

The target schema consists of 9 normalized tables with enforced primary keys, foreign keys, constraints, and operation tracking tables.

```mermaid
erDiagram
    Customers ||--o{ Accounts : "owns"
    Customers }|--|| Addresses : "resides at"
    Accounts ||--o{ Transactions : "contains"
    Accounts ||--o{ Loans : "associated with"
    Customers ||--o{ Beneficiaries : "designates"
    MigrationRuns ||--o{ MigrationExceptions : "tracks exceptions for"
    MigrationRuns ||--o{ MigrationAudit : "records audit entries for"

    Customers {
        string customer_id PK
        string full_name
        date date_of_birth
        string phone_number
        string email
        string address_id FK
        datetime created_at
    }

    Accounts {
        string account_id PK
        string customer_id FK
        string account_type
        decimal balance
        date opened_date
        string status
        datetime created_at
    }

    Transactions {
        string transaction_id PK
        string account_id FK
        string transaction_type
        decimal amount
        datetime transaction_date
        string description
        datetime created_at
    }

    Loans {
        string loan_id PK
        string account_id FK
        decimal loan_amount
        decimal interest_rate
        int term_months
        date start_date
        datetime created_at
    }

    Beneficiaries {
        string beneficiary_id PK
        string customer_id FK
        string beneficiary_name
        string account_number
        string routing_code
        datetime created_at
    }

    Addresses {
        string address_id PK
        string street_address
        string city
        string state
        string postal_code
        string country
        datetime created_at
    }

    MigrationRuns {
        string run_id PK
        datetime started_at
        datetime completed_at
        int source_records
        int validated_records
        int transformed_records
        int loaded_records
        int rejected_records
        string status
    }

    MigrationExceptions {
        int exception_id PK
        string run_id FK
        string entity_type
        string record_id
        string rule_id
        string severity
        string error_message
        string source_data
        datetime created_at
        string status
    }

    MigrationAudit {
        int audit_id PK
        string run_id FK
        string entity
        string record_id
        string operation
        datetime timestamp
        string status
    }
```

---

## Field-Mapping Catalog

| Entity | Legacy Field | Target Field | Data Type Transformation | Cleaning / Normalization Rule |
| :--- | :--- | :--- | :--- | :--- |
| **Customer** | `customer_id` | `customer_id` | `NVARCHAR(50)` | Trim whitespace; reject NULL or empty |
| **Customer** | `customer_name` | `full_name` | `NVARCHAR(100)` | Strip spaces, convert to Title Case (`john smith` $\rightarrow$ `John Smith`) |
| **Customer** | `dob` | `date_of_birth` | `DATE` | Parse multi-format dates (`DD/MM/YYYY`, `YYYY-MM-DD`, `MM-DD-YYYY`) to ISO `YYYY-MM-DD` |
| **Customer** | `phone` | `phone_number` | `NVARCHAR(20)` | Strip non-digits (`+91-`, spaces); enforce 10-12 digit format |
| **Customer** | `email` | `email` | `NVARCHAR(100)` | Trim, convert to lowercase, validate regex format (`user@domain.com`) |
| **Customer** | `address_id` | `address_id` | `NVARCHAR(50)` | Foreign key reference to Addresses table |
| **Account** | `account_id` | `account_id` | `NVARCHAR(50)` | Primary Key; trim whitespace |
| **Account** | `customer_id` | `customer_id` | `NVARCHAR(50)` | Foreign Key check against valid Target Customers |
| **Account** | `account_type` | `account_type` | `NVARCHAR(20)` | Normalize to UPPERCASE (`SAVINGS`, `CHECKING`, `LOAN`) |
| **Account** | `balance` | `balance` | `DECIMAL(18,2)` | Validate non-negative for Savings/Checking |
| **Account** | `opened_date` | `opened_date` | `DATE` | Parse to ISO `YYYY-MM-DD` |
| **Account** | `status` | `status` | `NVARCHAR(20)` | Upper Case (`ACTIVE`, `CLOSED`, `DORMANT`) |
| **Transaction** | `transaction_id` | `transaction_id` | `NVARCHAR(50)` | Primary Key; trim whitespace |
| **Transaction** | `account_id` | `account_id` | `NVARCHAR(50)` | Foreign Key check against valid Target Accounts |
| **Transaction** | `transaction_type` | `transaction_type` | `NVARCHAR(20)` | Upper Case (`DEPOSIT`, `WITHDRAWAL`, `TRANSFER`) |
| **Transaction** | `amount` | `amount` | `DECIMAL(18,2)` | Must be non-zero positive number |
| **Transaction** | `transaction_date` | `transaction_date` | `DATETIME2` | Parse date/time string to standard timestamp |
| **Transaction** | `description` | `description` | `NVARCHAR(255)` | Clean trailing spaces |
