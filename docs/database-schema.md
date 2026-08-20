# BankMigrate — Database Schema & Data Dictionary

## 1. Legacy Schema (`BankMigrate_Legacy`)
The legacy database schema consists of 6 unconstrained tables without SQL `PRIMARY KEY` or `FOREIGN KEY` definitions. All fields are defined as `NVARCHAR` and `NULLable` to simulate dirty legacy enterprise data.

```mermaid
erDiagram
    Customers_Legacy {
        string customer_id
        string customer_name
        string dob
        string phone
        string email
        string street
        string city
        string state
        string zip
    }
    Accounts_Legacy {
        string account_id
        string customer_id
        string account_type
        string balance
        string open_date
        string status
    }
    Transactions_Legacy {
        string transaction_id
        string account_id
        string txn_type
        string amount
        string txn_date
        string remarks
    }
    Loans_Legacy {
        string loan_id
        string account_id
        string amount
        string rate
        string term
        string start_date
    }
    Beneficiaries_Legacy {
        string beneficiary_id
        string customer_id
        string name
        string account_no
        string routing
    }
    Addresses_Legacy {
        string address_id
        string street
        string city
        string state
        string zip
        string country
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
        string address_id PK
        string street_address
        string city
        string state
        string postal_code
        string country
        datetime created_at
    }

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
