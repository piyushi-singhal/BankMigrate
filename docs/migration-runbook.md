# Migration Execution Runbook

## Overview
This runbook documents the step-by-step procedures required to execute, monitor, and verify a migration batch run using BankMigrate.

---

## Migration Call Sequence

The sequence diagram below visualizes the execution flow between ASP.NET Core API, Python Migration Engine, SQL Server databases, and the Exception Store.

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Operator / API Client
    participant API as ASP.NET Core API
    participant Py as Python Engine
    participant LDB as BankMigrate_Legacy (SQL Server)
    participant TDB as BankMigrate_Target (SQL Server)
    participant EX as Exception Store (MigrationExceptions)

    Admin->>API: POST /api/migrations (Trigger Migration Run)
    API->>TDB: Create MigrationRuns Record (Status: IN_PROGRESS)
    API->>Py: Invoke Migration Pipeline (`python -m migration_engine.main --run-id RUN-xxx`)
    
    activate Py
    Py->>LDB: Extract Customers, Accounts, Transactions Data
    LDB-->>Py: Return Raw Legacy DataFrames
    
    Py->>Py: Profile Data (Row Counts, Null Counts, Duplicates)
    Py->>Py: Execute Validation Engine Rules (CUSTOMER_*, ACCOUNT_*, TXN_*)
    
    alt Invalid Record Detected (e.g. TXN_002 / Account A999999 missing)
        Py->>EX: Write Rejected Record to MigrationExceptions (Rule ID, Source Data, Status: OPEN)
    end
    
    Py->>Py: Apply Transformations (Casing, ISO Date Parsing, Phone Normalization)
    Py->>TDB: Bulk Insert Clean Records (Customers, Accounts, Transactions)
    Py->>TDB: Execute Stored Procedure `sp_reconcile_migration`
    TDB-->>Py: Return Reconciliation Metrics (Source = Valid + Rejected Math)
    
    Py->>TDB: Write Audit Trail Entries (`MigrationAudit`)
    Py-->>API: Pipeline Execution Complete (Exit Code 0)
    deactivate Py
    
    API->>TDB: Update MigrationRuns (Status: COMPLETED_WITH_EXCEPTIONS)
    API-->>Admin: 200 OK (Run Summary & Metrics JSON)
```

---

## Step-by-Step Execution Guide

### Step 1: Verify Source Database
Connect to SQL Server and verify source tables contain data:
```sql
USE BankMigrate_Legacy;
SELECT COUNT(*) FROM Customers_Legacy;
SELECT COUNT(*) FROM Accounts_Legacy;
SELECT COUNT(*) FROM Transactions_Legacy;
```

### Step 2: Validate Connectivity
Ensure environment variables are configured in `.env`:
```env
DB_HOST=localhost
DB_PORT=1433
DB_USER=sa
DB_PASSWORD=BankMigrate123!
```
Run connectivity check:
```bash
./venv/bin/python -m migration_engine.config
```

### Step 3: Create Migration Run
Trigger migration via HTTP POST request to API endpoint:
```bash
curl -X POST http://localhost:5000/api/migrations
```

### Step 4: Execute Extraction
The Python engine extracts legacy records from `BankMigrate_Legacy` into Pandas DataFrames.

### Step 5: Run Validation
Applies rules from `docs/validation-rules.md` to split records into `Valid` and `Invalid` DataFrames.

### Step 6: Review Exceptions
Query isolated exceptions via API or SQL:
```bash
curl http://localhost:5000/api/migrations/RUN-20260821-001/exceptions
```

### Step 7: Transform Valid Records
Cleans casing, formats dates to ISO standards, normalizes phone numbers.

### Step 8: Load Target
Performs transactional bulk inserts into `BankMigrate_Target`.

### Step 9: Run Reconciliation
Executes `sp_reconcile_migration` to verify mathematical balance:
$$\text{Source Count} = \text{Valid Count} + \text{Rejected Count}$$

### Step 10: Review Migration Report
Retrieve final summary report:
```bash
curl http://localhost:5000/api/migrations/RUN-20260821-001/reconciliation
```
