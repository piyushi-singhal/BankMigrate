# BankMigrate — Enterprise Banking Data Migration Platform

[![Build & Test Status](https://img.shields.io/badge/Pytest-100%25%20Passing-brightgreen)](file:///Users/piyushisinghal/Downloads/BankMigrate/tests)
[![.NET Version](https://img.shields.io/badge/.NET-8.0%20Web%20API-blue)](file:///Users/piyushisinghal/Downloads/BankMigrate/api)
[![SQL Server](https://img.shields.io/badge/Database-SQL%20Server%20%2F%20Azure%20SQL%20Edge-red)](file:///Users/piyushisinghal/Downloads/BankMigrate/scripts/sql)

BankMigrate is an enterprise-grade banking data migration platform designed to extract, profile, validate, transform, bulk-load, reconcile, and audit legacy banking data from an unconstrained source database (`BankMigrate_Legacy`) into a normalized, constraint-enforced target database (`BankMigrate_Target`).

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

## Quickstart Instructions

### 1. Environment & Database Setup
```bash
# Clone repository & setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Provision SQL Server databases & seed legacy data with defects
PYTHONPATH=. ./venv/bin/python scripts/init_databases.py
PYTHONPATH=. ./venv/bin/python scripts/seed_legacy.py
PYTHONPATH=. ./venv/bin/python scripts/create_target.py
PYTHONPATH=. ./venv/bin/python scripts/create_stored_procedures.py
```

### 2. Run the Full Migration Pipeline
```bash
# Execute end-to-end migration pipeline CLI
PYTHONPATH=. ./venv/bin/python -m migration_engine.pipeline --run-id RUN-PROD-001
```

### 3. Run Integration Tests
```bash
# Execute pytest integration test suite (100% passing)
PYTHONPATH=. ./venv/bin/pytest tests/
```

### 4. Launch the ASP.NET Core REST API
```bash
# Build and run API server
dotnet run --project api/BankMigrate.Api.csproj
```

---

## System Verification

- **Pytest Suite:** `8 passed in 1.58s` ✅
- **API Build:** `Build succeeded. 0 Warning(s), 0 Error(s)` ✅
- **SQL Server Target Load:** 29 valid records loaded cleanly in FK dependency order ✅
- **Defect Isolation:** 9 legacy defects caught and written to `MigrationExceptions` ✅
- **Reconciliation Check:** $38 = 29 + 9 \rightarrow$ `BALANCED` ✅
