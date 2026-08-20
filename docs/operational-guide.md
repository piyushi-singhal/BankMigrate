# BankMigrate — Operational & Deployment Guide

## 1. Environment Setup & Prerequisites
- **Database Server:** Microsoft SQL Server 2019+ or Azure SQL Edge running on Docker (exposed on port `1433`).
- **Python Engine:** Python 3.14+ (virtual environment at `./venv`). Required packages: `pandas`, `sqlalchemy`, `pymssql`, `pytest`, `apscheduler`, `python-dotenv`.
- **API Runtime:** .NET 8.0 SDK (`dotnet`).

---

## 2. Initialization & Database Setup

```bash
# 1. Initialize Python Virtual Environment & Install Dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Provision SQL Server Databases (BankMigrate_Legacy & BankMigrate_Target)
PYTHONPATH=. ./venv/bin/python scripts/init_databases.py

# 3. Create & Seed Legacy Schema with Defect Data
PYTHONPATH=. ./venv/bin/python scripts/seed_legacy.py

# 4. Create Target Schema & Operational Tracking Tables
PYTHONPATH=. ./venv/bin/python scripts/create_target.py

# 5. Deploy T-SQL Stored Procedures & Security Role
PYTHONPATH=. ./venv/bin/python scripts/create_stored_procedures.py
```

---

## 3. Running the Migration Engine

### Option A: Direct Python Pipeline CLI Execution
```bash
# Run complete end-to-end migration pipeline
PYTHONPATH=. ./venv/bin/python -m migration_engine.pipeline --run-id RUN-PROD-001
```

### Option B: Automated Scheduling Engine
```bash
# Start background recurring cron scheduler (runs every N minutes)
PYTHONPATH=. ./venv/bin/python scheduler/migration_scheduler.py
```

### Option C: ASP.NET Core REST API Server
```bash
# Build and run the ASP.NET Core API server (port 5000 / 5001)
dotnet run --project api/BankMigrate.Api.csproj
```

---

## 4. ASP.NET Core REST API Endpoint Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/migrations` | Triggers a new migration run asynchronously. |
| `GET` | `/api/migrations` | Lists all past and current migration runs. |
| `GET` | `/api/migrations/{runId}` | Gets status and detailed metrics for a specific run. |
| `GET` | `/api/migrations/{runId}/exceptions` | Lists all isolated rejected records for a run. |
| `GET` | `/api/migrations/{runId}/reconciliation` | Retrieves count and monetary amount reconciliation report. |
| `POST` | `/api/migrations/{runId}/retry` | Retries a failed or partially completed run. |

---

## 5. Exception Handling & Disaster Recovery Workflow

1. **Inspecting Exceptions:** Query `MigrationExceptions` via T-SQL or `GET /api/migrations/{runId}/exceptions`.
2. **Reviewing Rule IDs:** Check assigned Rule IDs (`CUSTOMER_001` through `CUSTOMER_005`, `ACCOUNT_001` through `ACCOUNT_004`, `TXN_001` through `TXN_005`).
3. **Reviewing Raw JSON Snapshots:** Inspect `source_data` column in `MigrationExceptions` to see the original offending legacy record.
4. **Triggering Retry Recovery:** Execute `POST /api/migrations/{runId}/retry` or `run_pipeline(run_id, clear_target=True)`. The pipeline safely clears dirty intermediate states and re-executes cleanly.

---

## 6. Running Integration Tests
```bash
# Execute full pytest integration test suite
PYTHONPATH=. ./venv/bin/pytest tests/
```
