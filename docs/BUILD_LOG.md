# BankMigrate — Engineering Build Log

## Milestone 1: Provision SQL Server & Create Dual Databases
**Date:** 2026-08-21  
**Status:** COMPLETE  

---

### 1. What Was Built
- **Infrastructure & Container Setup:** Provisioned Microsoft SQL Server (Azure SQL Edge container `mcr.microsoft.com/azure-sql-edge:latest` running on Docker via Colima, exposed on port `1433`).
- **Database Provisioning:** Executed T-SQL DDL to create two isolated relational databases:
  1. `BankMigrate_Legacy`: The source database hosting unvalidated, non-normalized legacy banking data.
  2. `BankMigrate_Target`: The destination database hosting clean, normalized target schemas, run tracking, exception logs, and audit trails.
- **Automation Scripting:** Created `scripts/sql/01_create_databases.sql` containing idempotent T-SQL DDL and `scripts/init_databases.py` using `pymssql` to verify connectivity, poll until SQL Server engine initialization completes, and execute the creation batches.

---

### 2. Why It Was Built This Way
- **Containerized SQL Server Engine:** Using Docker (Azure SQL Edge on ARM64 macOS) provides a lightweight, enterprise-identical SQL Server instance without needing local OS-level SQL Server installation or cloud dependencies.
- **Strict Database Separation:** `BankMigrate_Legacy` and `BankMigrate_Target` are kept as completely distinct databases (rather than separate schemas in one database) to simulate real-world enterprise banking migrations where legacy and core banking systems reside on separate database servers or standalone engines.
- **Idempotent T-SQL DDL:** Used `IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = ...)` guards in T-SQL to guarantee that re-running deployment or initialization scripts will not fail or drop existing database states.
- **Python-driven Initialization:** Built `scripts/init_databases.py` with exponential backoff polling (`wait_for_sql_server`) to handle cold-start container initialization, ensuring robust automated setup in CI/CD or local developer environments.

---

### 3. How It Was Built
- **T-SQL Script (`scripts/sql/01_create_databases.sql`):**
  ```sql
  IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'BankMigrate_Legacy')
  BEGIN
      CREATE DATABASE BankMigrate_Legacy;
      PRINT 'Database BankMigrate_Legacy created successfully.';
  END
  GO

  IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'BankMigrate_Target')
  BEGIN
      CREATE DATABASE BankMigrate_Target;
      PRINT 'Database BankMigrate_Target created successfully.';
  END
  GO
  ```
- **Connection Logic & Polling (`scripts/init_databases.py`):**
  Connected using `pymssql.connect()` with `autocommit=True` to Master database context (`sa` user credentials), parsed T-SQL batches delimited by `GO`, and queried `sys.databases` to verify presence of both database catalog entries.
- **Verification Result:** Querying `sys.databases` confirmed both catalogs: `['BankMigrate_Legacy', 'BankMigrate_Target']`.

---

### 4. Tech Stack Used in This Step
- **Database Engine:** Microsoft SQL Server (Azure SQL Edge Docker container `mcr.microsoft.com/azure-sql-edge:latest`)
- **Container Host:** Docker 28.x via Colima (vz driver, macOS ARM64)
- **Language / Runtime:** Python 3.14.5 (virtual environment at `./venv`)
- **Database Driver:** `pymssql` 2.3.13
- **Configuration Management:** `python-dotenv` 1.2.3 reading `.env`
