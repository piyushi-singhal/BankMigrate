# System Architecture

## Overview
BankMigrate is an enterprise banking data migration platform designed to simulate moving inconsistent legacy banking data into a clean, normalized target system. The architecture decouples orchestration, data processing, and persistence into clear technical layers:

1. **Orchestration & REST Layer:** ASP.NET Core Web API (.NET 8 C#)
2. **Data Processing Engine:** Python 3.x with Pandas, SQLAlchemy, and T-SQL Stored Procedures
3. **Relational Storage:** Microsoft SQL Server hosting `BankMigrate_Legacy` and `BankMigrate_Target`

---

## 4.1 End-to-End Data Flow

The data pipeline processes legacy data sequentially through seven pipeline stages:

```mermaid
flowchart TD
    subgraph LegacyStorage ["Legacy Storage"]
        LDB[("Legacy SQL Server Database\n(BankMigrate_Legacy)")]
    end

    subgraph Pipeline ["Python Migration Engine"]
        EXT["1. Data Extraction\n(SQL queries to DataFrames)"]
        PROF["2. Data Profiling\n(Row, Null, Duplicate Counts)"]
        VAL{"3. Data Validation\n(Rule Engine Check)"}
        TRANS["4. Transformation\n(Casing, Formatting, Cleaning)"]
        LOAD["5. Target Load\n(Inserts to Target Tables)"]
        RECON["6. Reconciliation\n(Count & Dollar Amount Math)"]
        REP["7. Migration Report\n(Run Status & Summaries)"]
    end

    subgraph TargetStorage ["Target & Audit Storage"]
        EX_STORE[("Exception Store\n(MigrationExceptions)")]
        TDB[("Target Database\n(BankMigrate_Target)")]
        AUDIT[("Audit Log\n(MigrationAudit & MigrationRuns)")]
    end

    LDB --> EXT
    EXT --> PROF
    PROF --> VAL
    VAL -->|Valid Records| TRANS
    VAL -->|Invalid Records| EX_STORE
    TRANS --> LOAD
    LOAD --> TDB
    TDB --> RECON
    EX_STORE --> RECON
    RECON --> REP
    REP --> AUDIT
```

---

## 4.2 Component / Service Architecture

The system decouples RESTful HTTP management from core batch migration processing:

```mermaid
graph TD
    subgraph Client ["Management Client / Consumer"]
        HTTP_REQ["HTTP REST Requests\n(cURL, Postman, Web Apps)"]
    end

    subgraph ApiLayer ["ASP.NET Core API (.NET 8)"]
        CTRL["Migration Controller"]
        SVC["Migration Service"]
        REP_SVC["Reporting Service"]
    end

    subgraph EngineLayer ["Python Migration Engine"]
        SUB_PROC["CLI Engine Invoker\n(main.py)"]
        MODULES["Engine Modules:\n• extraction/\n• profiling/\n• validation/\n• transformation/\n• loading/\n• reconciliation/\n• exceptions/\n• audit/"]
    end

    subgraph SqlLayer ["Microsoft SQL Server Engine"]
        SP_LAYER["T-SQL Stored Procedures:\n• sp_validate_customers\n• sp_validate_accounts\n• sp_validate_transactions\n• sp_detect_duplicates\n• sp_reconcile_migration\n• sp_generate_migration_summary"]
        
        DB_LEGACY[("BankMigrate_Legacy\n• Customers_Legacy\n• Accounts_Legacy\n• Transactions_Legacy\n• Loans_Legacy\n• Beneficiaries_Legacy\n• Addresses_Legacy")]
        
        DB_TARGET[("BankMigrate_Target\n• Customers\n• Accounts\n• Transactions\n• Loans\n• Beneficiaries\n• Addresses\n• MigrationRuns\n• MigrationExceptions\n• MigrationAudit")]
    end

    HTTP_REQ --> CTRL
    CTRL --> SVC
    CTRL --> REP_SVC
    SVC --> SUB_PROC
    SUB_PROC --> MODULES
    MODULES --> SP_LAYER
    MODULES --> DB_LEGACY
    MODULES --> DB_TARGET
    REP_SVC --> DB_TARGET
```

---

## Architecture Rationale
- **ASP.NET Core REST API:** Exposes endpoints to start, list, inspect, and retry migration runs without embedding heavyweight data processing inside web server threads.
- **Python Engine:** Utilizes Pandas for high-speed in-memory cleaning, transformation, and validation rule enforcement across large datasets.
- **T-SQL Stored Procedures:** Leverages SQL Server's native engine for set-based validation, window-function duplicate detection (`ROW_NUMBER()`), and atomic audit transactions.
