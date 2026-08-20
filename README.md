# BankMigrate — Enterprise Banking Data Migration Platform

[![Build & Test Status](https://img.shields.io/badge/Pytest-100%25%20Passing-brightgreen)](tests/)
[![.NET Version](https://img.shields.io/badge/.NET-8.0%20Web%20API-blue)](api/)
[![SQL Server](https://img.shields.io/badge/Database-SQL%20Server%20%2F%20Azure%20SQL%20Edge-red)](scripts/sql/)

BankMigrate is an enterprise-grade banking data migration platform designed to extract, profile, validate, transform, bulk-load, reconcile, and audit legacy banking data from an unconstrained source database (`BankMigrate_Legacy`) into a normalized, constraint-enforced target database (`BankMigrate_Target`).

---

## System Architecture

```mermaid
graph TD
    subgraph Source_Layer ["Source Layer"]
        LegacyDB["BankMigrate_Legacy Database - 6 Unconstrained Legacy Tables"]
    end

    subgraph Core_Engine ["Core Migration Engine (Python)"]
        Ext["1. Extractor Module"]
        Prof["2. Profiler Module"]
        Val["3. Validator Module & Rule Catalog"]
        Trans["4. Transformer Module"]
        Load["5. Target Bulk Loader"]
        Recon["6. Reconciliation Engine"]
        Audit["7. Audit & Run Logger"]
        Exc["8. Exception Handler"]
    end

    subgraph DB_Layer ["Destination & Operations Layer (SQL Server)"]
        TargetDB["BankMigrate_Target Database"]
        RunsTab["MigrationRuns Table"]
        ExTab["MigrationExceptions Store"]
        AuditTab["MigrationAudit Trail"]
        SPs["T-SQL Stored Procedures"]
    end

    subgraph Control_Layer ["Control & Orchestration Layer"]
        API["ASP.NET Core REST API Controller"]
        Sched["APScheduler Background Worker"]
    end

    LegacyDB --> Ext
    Ext --> Prof
    Prof --> Val
    Val --> Exc
    Exc --> ExTab
    Val --> Trans
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
