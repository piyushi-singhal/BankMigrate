# BankMigrate — Enterprise Banking Data Migration Platform

[![Build & Test Status](https://img.shields.io/badge/Pytest-100%25%20Passing-brightgreen)](file:///Users/piyushisinghal/Downloads/BankMigrate/tests)
[![.NET Version](https://img.shields.io/badge/.NET-8.0%20Web%20API-blue)](file:///Users/piyushisinghal/Downloads/BankMigrate/api)
[![SQL Server](https://img.shields.io/badge/Database-SQL%20Server%20%2F%20Azure%20SQL%20Edge-red)](file:///Users/piyushisinghal/Downloads/BankMigrate/scripts/sql)

BankMigrate is an enterprise-grade banking data migration platform designed to extract, profile, validate, transform, bulk-load, reconcile, and audit legacy banking data from an unconstrained source database (`BankMigrate_Legacy`) into a normalized, constraint-enforced target database (`BankMigrate_Target`).

---

## System Architecture

```mermaid
graph TD
    subgraph Source Layer
        LegacyDB[BankMigrate_Legacy Database<br/>6 Unconstrained Legacy Tables]
    end

    subgraph Core Migration Engine (Python)
        Ext[1. Extractor Module]
        Prof[2. Profiler Module]
        Val[3. Validator Module & Rule Catalog]
        Trans[4. Transformer Module]
        Load[5. Target Bulk Loader]
        Recon[6. Reconciliation Engine]
        Audit[7. Audit & Run Logger]
        Exc[8. Exception Handler]
    end

    subgraph Destination & Operations Layer (SQL Server)
        TargetDB[BankMigrate_Target Database]
        RunsTab[(MigrationRuns Table)]
        ExTab[(MigrationExceptions Store)]
        AuditTab[(MigrationAudit Trail)]
        SPs[T-SQL Stored Procedures]
    end

    subgraph Control & Orchestration Layer
        API[ASP.NET Core REST API Controller]
        Sched[APScheduler Background Worker]
    end

    LegacyDB --> Ext
    Ext --> Prof
    Prof --> Val
    Val -- Isolated Defects --> Exc
    Exc --> ExTab
    Val -- Valid Records --> Trans
    Trans --> Load
    Load --> TargetDB
    Load --> AuditTab
    Audit --> RunsTab
    TargetDB --> SPs
    SPs --> Recon
    API --> Ext
    API --> RunsTab
    API --> ExTab
    Sched --> Ext
```

---

## Entity-Relationship (ER) Diagrams

### 1. Source Schema (`BankMigrate_Legacy`)
Unconstrained, non-normalized legacy banking tables with `NVARCHAR` types and deliberate data quality defects.

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

### 2. Target Normalized Schema (`BankMigrate_Target`)
Clean 3NF banking domain model enforcing primary keys, foreign keys, explicit data types (`DATE`, `DATETIME2`, `DECIMAL(18,2)`), and operational tracking tables.

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

## Pipeline Execution Sequence

```mermaid
sequenceDiagram
    autonumber
    participant Client as API Client / Operator
    participant API as ASP.NET Core REST API
    participant Pipeline as Python Pipeline Engine
    participant Legacy as BankMigrate_Legacy DB
    participant Target as BankMigrate_Target DB
    participant SP as T-SQL Stored Procedures

    Client->>API: POST /api/migrations
    API->>Pipeline: Trigger run_pipeline(run_id)
    Pipeline->>Target: INSERT INTO MigrationRuns (status='IN_PROGRESS')
    Pipeline->>Legacy: SELECT * FROM Legacy Tables
    Legacy-->>Pipeline: Raw Legacy DataFrames (38 records)
    Pipeline->>Pipeline: Validate Rule Catalog (CUSTOMER_*, ACCOUNT_*, TXN_*)
    Pipeline->>Target: INSERT INTO MigrationExceptions (9 Isolated Defects)
    Pipeline->>Pipeline: Transform Valid Data (Title Case, ISO Dates, Enums)
    Pipeline->>Target: FK-Ordered Bulk Load (Addresses -> Customers -> Accounts -> Txns)
    Pipeline->>Target: INSERT INTO MigrationAudit (74 Atomic DML Events)
    Pipeline->>SP: EXEC sp_reconcile_migration(@RunId)
    SP-->>Pipeline: Monetary Balance Report (BALANCED)
    Pipeline->>Target: UPDATE MigrationRuns (status='COMPLETED_WITH_EXCEPTIONS')
    Pipeline-->>API: Pipeline Result JSON
    API-->>Client: 200 OK (Run Summary)
```

---

## Key Features

- **Dual-Layer Validation:** Python application-level rule engine + T-SQL stored procedures (`sp_validate_customers`, `sp_validate_accounts`, `sp_validate_transactions`, `sp_detect_duplicates`).
- **Defect Isolation Store:** Preserves 100% of rejected records in `MigrationExceptions` with immutable Rule IDs and raw JSON source snapshots. Zero silent data loss.
- **Automated Financial Reconciliation:** Verifies mathematical count balance ($\text{Source} = \text{Valid} + \text{Rejected}$) and monetary balance via `sp_reconcile_migration` ($\text{Source Txn Sum} = \text{Target Txn Sum} + \text{Rejected Txn Sum}$).
- **ASP.NET Core REST API:** .NET 8 Web API providing RESTful management and reporting endpoints (`GET /api/migrations`, `GET /api/migrations/{runId}/exceptions`, `GET /api/migrations/{runId}/reconciliation`, `POST /api/migrations/{runId}/retry`).
- **Automated Background Scheduler:** Cron & interval recurring batch execution using `APScheduler`.
- **Failure Recovery & Disaster Resilience:** Catches network drops or table lock timeouts (`NETWORK_DROP`, `LOCKED_TABLE`), transitions run state to `FAILED`, and recovers cleanly via retry.
- **Security Hardened:** Least-privilege SQL Server role (`bankmigrate_app_role`), 100% query parameterization, dynamic environment secrets, PII masking (`sanitizer.py`).

---

## Repository Structure

```text
BankMigrate/
├── api/                            # ASP.NET Core 8 Web API (.NET 8 C#)
│   ├── Controllers/MigrationController.cs
│   ├── Services/ReportingService.cs & MigrationService.cs
│   └── Models/MigrationModels.cs
├── docs/                           # Living Documentation Package
│   ├── BUILD_LOG.md                # Engineering build log for all 20 milestones
│   ├── architecture.md             # System architecture & Mermaid sequence diagrams
│   ├── database-schema.md          # ER diagrams for Legacy and Target schemas
│   ├── data-mapping.md             # Data mapping catalog & transformation specifications
│   └── operational-guide.md        # Deployment & operations manual
├── migration_engine/               # Core Python Data Migration Engine
│   ├── config/                     # Settings & Database connection management
│   ├── extraction/                 # Legacy SQL extraction to Pandas DataFrames
│   ├── profiling/                  # Anomaly profiling & duplicate detection
│   ├── validation/                 # Rule catalog & entity validation engine
│   ├── transformation/             # Data cleaning, ISO dates, Title Case, normalizations
│   ├── loading/                    # FK-ordered bulk loading into target SQL Server
│   ├── reconciliation/             # Count math & monetary balance reconciliation
│   ├── exceptions/                 # Exception store & failure simulator
│   ├── audit/                      # MigrationRuns & MigrationAudit logging
│   └── pipeline.py                 # Full end-to-end pipeline orchestrator
├── scheduler/                      # APScheduler automated background scheduler
├── scripts/                        # Database setup & milestone verification scripts
│   └── sql/                        # T-SQL DDL, stored procedures, & security scripts
└── tests/                          # Pytest end-to-end integration test suite
```

---

## System Verification Metrics

- **Pytest Integration Suite:** `8 passed in 1.58s` ✅
- **ASP.NET Core API Build:** `Build succeeded. 0 Warning(s), 0 Error(s)` ✅
- **SQL Server Target Load:** 29 valid records loaded cleanly in FK dependency order ✅
- **Defect Isolation Store:** 9 legacy defects caught and written to `MigrationExceptions` ✅
- **Financial Reconciliation Check:** Source (38) = Valid (29) + Rejected (9) $\rightarrow$ `BALANCED` ✅
