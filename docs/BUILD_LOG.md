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
  Executed database creation batches with database presence checks.
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

---

## Milestone 2: Create & Seed Legacy Schema with Intentional Data Quality Problems
**Date:** 2026-08-21  
**Status:** COMPLETE  

---

### 1. What Was Built
- **Legacy Database Schema:** Created all 6 legacy source tables in database `BankMigrate_Legacy`:
  1. `Addresses_Legacy` (5 records)
  2. `Customers_Legacy` (11 records)
  3. `Accounts_Legacy` (8 records)
  4. `Transactions_Legacy` (10 records)
  5. `Loans_Legacy` (2 records)
  6. `Beneficiaries_Legacy` (2 records)
- **Synthetic Data Seeding Scripting:** Developed `scripts/sql/02_create_seed_legacy.sql` to define unconstrained legacy tables and populate synthetic banking data containing deliberate data-quality defects traceable to Section 7 of the PDF spec.
- **Database Seeder & Verification Suite:** Created `scripts/seed_legacy.py` to execute table creation and row inserts, and `scripts/verify_legacy_defects.py` to query and prove every seeded data-quality defect.

---

### 2. Why It Was Built This Way
- **Unconstrained Legacy Tables:** The legacy tables intentionally omit SQL `PRIMARY KEY` and `FOREIGN KEY` constraints (defining columns as `NVARCHAR` and `NULLable`). In real enterprise migrations, legacy databases often contain orphaned references, duplicate natural keys, and missing fields. Omitting strict engine constraints allows dirty data to exist in `BankMigrate_Legacy` so the Python migration and T-SQL validation engine can detect and isolate them.
- **Documented, Deterministic Quality Defects:** Rather than generating random noise, data defects were seeded deterministically to match Section 7 of the specification:
  - **Duplicate Customers (`CUSTOMER_002`):** `C001` ('john smith', '1985-05-15') vs `C019` ('JOHN SMITH', '1985-05-15').
  - **Missing Mandatory Field (`CUSTOMER_001`):** Customer record with `customer_id = NULL` ('Jane Doe').
  - **Invalid Email Format (`CUSTOMER_004`):** `C006` email set to `'charlie_brown_at_domain.com'`.
  - **Invalid Date of Birth (`CUSTOMER_005`):** `C007` DOB set to unparseable string `'31/02/1999'`.
  - **Invalid Negative Balance (`ACCOUNT_004`):** Savings Account `A004` balance set to `-500.00`.
  - **Orphan Foreign Key (`ACCOUNT_002`):** Account `A010` referencing nonexistent customer `C999`.
  - **Duplicate Transaction (`TXN_005`):** Transaction `TXN-1005` inserted twice identically.
  - **Orphan Transaction Foreign Key (`TXN_002`):** Transaction `TXN-89231` referencing nonexistent account `A999999`.
  - **Invalid Transaction Amount (`TXN_003`):** Transaction `TXN-1008` amount set to `-100.00`.

---

### 3. How It Was Built
- **T-SQL DDL & Seeding (`scripts/sql/02_create_seed_legacy.sql`):**
  Executed `DROP TABLE` conditional checks followed by `CREATE TABLE` scripts defining flexible columns. Populated tables using parameterized explicit column `INSERT INTO TableName (col1, col2, ...) VALUES (...)` statements.
- **Python Execution & Verification (`scripts/seed_legacy.py` & `scripts/verify_legacy_defects.py`):**
  `seed_legacy.py` connects to `BankMigrate_Legacy` via `pymssql`, drops/re-creates tables, parses line-by-line inserts, and verifies row counts. `verify_legacy_defects.py` runs targeted `SELECT` queries for each defect rule (`CUSTOMER_*`, `ACCOUNT_*`, `TXN_*`) to output verification details.
- **Verification Output:**
  ```text
  Table 'Addresses_Legacy': 5 total rows seeded.
  Table 'Customers_Legacy': 11 total rows seeded.
  Table 'Accounts_Legacy': 8 total rows seeded.
  Table 'Beneficiaries_Legacy': 2 total rows seeded.
  Table 'Loans_Legacy': 2 total rows seeded.
  Table 'Transactions_Legacy': 10 total rows seeded.
  ```

---

### 4. Tech Stack Used in This Step
- **Database Engine:** Microsoft SQL Server (Azure SQL Edge container `mcr.microsoft.com/azure-sql-edge:latest`)
- **Database Driver:** `pymssql` 2.3.13
- **SQL Scripting:** T-SQL (Table creation, `INFORMATION_SCHEMA`, aggregation queries)
- **Language / Runtime:** Python 3.14.5
- **Configuration Management:** `python-dotenv` 1.2.3 reading `.env`
