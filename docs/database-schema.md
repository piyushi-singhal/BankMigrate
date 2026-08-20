# BankMigrate — Database Schema & Data Dictionary

## 1. Legacy Schema (`BankMigrate_Legacy`)
The legacy database schema consists of 6 unconstrained tables without SQL `PRIMARY KEY` or `FOREIGN KEY` definitions. All fields are defined as `NVARCHAR` and `NULLable` to simulate dirty legacy enterprise data.

```mermaid
erDiagram
    Customers_Legacy {
        NVARCHAR customer_id
        NVARCHAR customer_name
        NVARCHAR dob
        NVARCHAR phone
        NVARCHAR email
        NVARCHAR street
        NVARCHAR city
        NVARCHAR state
        NVARCHAR zip
    }
    Accounts_Legacy {
        NVARCHAR account_id
        NVARCHAR customer_id
        NVARCHAR account_type
        NVARCHAR balance
        NVARCHAR open_date
        NVARCHAR status
    }
    Transactions_Legacy {
        NVARCHAR transaction_id
        NVARCHAR account_id
        NVARCHAR txn_type
        NVARCHAR amount
        NVARCHAR txn_date
        NVARCHAR remarks
    }
    Loans_Legacy {
        NVARCHAR loan_id
        NVARCHAR account_id
        NVARCHAR amount
        NVARCHAR rate
        NVARCHAR term
        NVARCHAR start_date
    }
    Beneficiaries_Legacy {
        NVARCHAR beneficiary_id
        NVARCHAR customer_id
        NVARCHAR name
        NVARCHAR account_no
        NVARCHAR routing
    }
    Addresses_Legacy {
        NVARCHAR address_id
        NVARCHAR street
        NVARCHAR city
        NVARCHAR state
        NVARCHAR zip
        NVARCHAR country
    }
```

---

## 2. Target & Operational Schema (`BankMigrate_Target`)
The target database schema consists of 6 normalized banking entity tables enforcing strict relational constraints (`PRIMARY KEY`, `FOREIGN KEY`, `NOT NULL`, explicit types) and 3 operational pipeline management tables.

```mermaid
erDiagram
    Addresses ||--o{ Customers : "has"
    Customers ||--o{ Accounts : "owns"
    Customers ||--o{ Beneficiaries : "designates"
    Accounts ||--o{ Transactions : "contains"
    Accounts ||--o{ Loans : "holds"

    MigrationRuns ||--o{ MigrationExceptions : "logs"
    MigrationRuns ||--o{ MigrationAudit : "tracks"

    Addresses {
        VARCHAR_50 address_id PK
        NVARCHAR_255 street_address
        NVARCHAR_100 city
        NVARCHAR_50 state
        NVARCHAR_20 postal_code
        NVARCHAR_50 country
        DATETIME2 created_at
    }

    Customers {
        VARCHAR_50 customer_id PK
        NVARCHAR_100 full_name
        DATE date_of_birth
        VARCHAR_20 phone_number
        VARCHAR_255 email
        VARCHAR_50 address_id FK
        DATETIME2 created_at
    }

    Accounts {
        VARCHAR_50 account_id PK
        VARCHAR_50 customer_id FK
        VARCHAR_20 account_type
        DECIMAL_18_2 balance
        DATE opened_date
        VARCHAR_20 status
        DATETIME2 created_at
    }

    Transactions {
        VARCHAR_50 transaction_id PK
        VARCHAR_50 account_id FK
        VARCHAR_20 transaction_type
        DECIMAL_18_2 amount
        DATETIME2 transaction_date
        NVARCHAR_255 description
        DATETIME2 created_at
    }

    Loans {
        VARCHAR_50 loan_id PK
        VARCHAR_50 account_id FK
        DECIMAL_18_2 loan_amount
        DECIMAL_5_2 interest_rate
        INT term_months
        DATE start_date
        DATETIME2 created_at
    }

    Beneficiaries {
        VARCHAR_50 beneficiary_id PK
        VARCHAR_50 customer_id FK
        NVARCHAR_100 beneficiary_name
        VARCHAR_50 account_number
        VARCHAR_50 routing_code
        DATETIME2 created_at
    }

    MigrationRuns {
        VARCHAR_50 run_id PK
        DATETIME2 started_at
        DATETIME2 completed_at
        INT source_records
        INT validated_records
        INT transformed_records
        INT loaded_records
        INT rejected_records
        VARCHAR_50 status
    }

    MigrationExceptions {
        INT exception_id PK
        VARCHAR_50 run_id FK
        VARCHAR_50 entity_type
        VARCHAR_50 record_id
        VARCHAR_50 rule_id
        VARCHAR_20 severity
        NVARCHAR_MAX error_message
        NVARCHAR_MAX source_data
        DATETIME2 created_at
        VARCHAR_20 status
    }

    MigrationAudit {
        INT audit_id PK
        VARCHAR_50 run_id FK
        VARCHAR_50 entity
        VARCHAR_50 record_id
        VARCHAR_50 operation
        DATETIME2 timestamp
        VARCHAR_20 status
    }
```

---

## 3. T-SQL Stored Procedure Catalog
1. `sp_detect_duplicates`: Uses window functions (`ROW_NUMBER() OVER (PARTITION BY ...)`).
2. `sp_validate_customers`: Customer validation using CTEs, `#CustExceptions`, and `TRY...CATCH`.
3. `sp_validate_accounts`: Account FK and balance validation.
4. `sp_validate_transactions`: Transaction validation.
5. `sp_reconcile_migration`: Calculates record count & monetary amount balance.
6. `sp_generate_migration_summary`: Produces run-level summary report.

---

## 4. Security & Indexing Strategy
- **Indexes:** Primary keys index automatically as clustered unique indexes. Foreign keys (`FK_Customers_Addresses`, `FK_Accounts_Customers`, `FK_Transactions_Accounts`) use non-clustered indexes for high-speed JOIN execution.
- **Least-Privilege Security Role:** `bankmigrate_app_role` created with `SELECT`, `INSERT`, `UPDATE`, `EXECUTE` privileges on target schema, denying `ALTER` or sysadmin access.
