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
- **Documented, Deterministic Quality Defects:** Rather than generating random noise, data defects were seeded deterministically to match Section 7 of the specification (`CUSTOMER_*`, `ACCOUNT_*`, `TXN_*`).

---

### 3. How It Was Built
- **T-SQL DDL & Seeding (`scripts/sql/02_create_seed_legacy.sql`):**
  Executed `DROP TABLE` conditional checks followed by `CREATE TABLE` scripts defining flexible columns. Populated tables using parameterized explicit column `INSERT INTO TableName (col1, col2, ...) VALUES (...)` statements.
- **Python Execution & Verification (`scripts/seed_legacy.py` & `scripts/verify_legacy_defects.py`):**
  `seed_legacy.py` connects to `BankMigrate_Legacy` via `pymssql`, drops/re-creates tables, parses line-by-line inserts, and verifies row counts. `verify_legacy_defects.py` runs targeted `SELECT` queries for each defect rule (`CUSTOMER_*`, `ACCOUNT_*`, `TXN_*`) to output verification details.

---

### 4. Tech Stack Used in This Step
- **Database Engine:** Microsoft SQL Server (Azure SQL Edge container `mcr.microsoft.com/azure-sql-edge:latest`)
- **Database Driver:** `pymssql` 2.3.13
- **SQL Scripting:** T-SQL (Table creation, `INFORMATION_SCHEMA`, aggregation queries)
- **Language / Runtime:** Python 3.14.5
- **Configuration Management:** `python-dotenv` 1.2.3 reading `.env`

---

## Milestone 3: Create Normalized Target Schema & Operational Tracking Tables
**Date:** 2026-08-21  
**Status:** COMPLETE  

---

### 1. What Was Built
- **Normalized Target Banking Schema:** Created 6 clean entity tables in `BankMigrate_Target`:
  1. `Addresses` (`address_id` PK, `street_address`, `city`, `state`, `postal_code`, `country`, `created_at`)
  2. `Customers` (`customer_id` PK, `full_name`, `date_of_birth` DATE, `phone_number`, `email`, `address_id` FK, `created_at`)
  3. `Accounts` (`account_id` PK, `customer_id` FK, `account_type`, `balance` DECIMAL(18,2), `opened_date` DATE, `status`, `created_at`)
  4. `Transactions` (`transaction_id` PK, `account_id` FK, `transaction_type`, `amount` DECIMAL(18,2), `transaction_date` DATETIME2, `description`, `created_at`)
  5. `Loans` (`loan_id` PK, `account_id` FK, `loan_amount` DECIMAL(18,2), `interest_rate` DECIMAL(5,2), `term_months`, `start_date` DATE, `created_at`)
  6. `Beneficiaries` (`beneficiary_id` PK, `customer_id` FK, `beneficiary_name`, `account_number`, `routing_code`, `created_at`)
- **Operational & Migration Infrastructure Tables:** Created 3 pipeline management tables in `BankMigrate_Target`:
  7. `MigrationRuns` (`run_id` PK, `started_at`, `completed_at`, `source_records`, `validated_records`, `transformed_records`, `loaded_records`, `rejected_records`, `status`)
  8. `MigrationExceptions` (`exception_id` IDENTITY PK, `run_id` FK, `entity_type`, `record_id`, `rule_id`, `severity`, `error_message`, `source_data`, `created_at`, `status`)
  9. `MigrationAudit` (`audit_id` IDENTITY PK, `run_id` FK, `entity`, `record_id`, `operation`, `timestamp`, `status`)
- **Automation & DDL Execution Scripts:** Created `scripts/sql/03_create_target_schema.sql` and `scripts/create_target.py` to execute batch creation and verify all 9 tables and foreign key constraints.

---

### 2. Why It Was Built This Way
- **Strict Referential Integrity & Typing:** Unlike `BankMigrate_Legacy`, the target schema enforces strict relational constraints (`PRIMARY KEY`, `FOREIGN KEY`, `NOT NULL`) and explicit banking data types (`DATE`, `DATETIME2`, `DECIMAL(18,2)`). This ensures invalid legacy data cannot bypass the validation layer and corrupt the target system.
- **Dedicated Operational Tracking Infrastructure:**
  - `MigrationRuns`: Provides run-level visibility, tracking record counts at each stage (`source` $\rightarrow$ `validated` $\rightarrow$ `transformed` $\rightarrow$ `loaded` $\rightarrow$ `rejected`) and run states (`IN_PROGRESS`, `COMPLETED`, `COMPLETED_WITH_EXCEPTIONS`, `FAILED`, `PARTIAL_FAILURE`).
  - `MigrationExceptions`: Acts as an exception store for isolated records, preserving a snapshot of offending raw JSON data alongside human-readable error messages and Rule IDs.
  - `MigrationAudit`: Serves as an append-only audit trail logging every atomic DML operation (`INSERT`, `UPDATE`, `REJECT`) per record.

---

### 3. How It Was Built
- **T-SQL DDL Scripting (`scripts/sql/03_create_target_schema.sql`):**
  Constructed DDL with reverse-dependency `DROP TABLE` checks and explicit relational constraints.
- **Python Setup & Inspection (`scripts/create_target.py`):**
  Executed T-SQL batches against `BankMigrate_Target` using `pymssql`. Verified table existence using `INFORMATION_SCHEMA.TABLES` and inspected enforced foreign key definitions via `sys.foreign_keys`.

---

### 4. Tech Stack Used in This Step
- **Database Engine:** Microsoft SQL Server (Azure SQL Edge container `mcr.microsoft.com/azure-sql-edge:latest`)
- **Database Driver:** `pymssql` 2.3.13
- **SQL Scripting:** T-SQL (DDL, `sys.foreign_keys`, `sys.tables`, `INFORMATION_SCHEMA`)
- **Language / Runtime:** Python 3.14.5
- **Configuration Management:** `python-dotenv` 1.2.3 reading `.env`

---

## Milestone 4: Write Formal Data Mapping & Transformation Specification
**Date:** 2026-08-21  
**Status:** COMPLETE  

---

### 1. What Was Built
- **Formal Data Mapping Catalog:** Expanded [`docs/data-mapping.md`](file:///Users/piyushisinghal/Downloads/BankMigrate/docs/data-mapping.md) into a comprehensive specification governing all 6 banking domain entities (`Customers`, `Accounts`, `Transactions`, `Loans`, `Beneficiaries`, `Addresses`).
- **Entity & Infrastructure ER Diagrams:** Updated visual Mermaid Entity-Relationship (ER) diagrams for both `BankMigrate_Legacy` (6 unconstrained legacy tables) and `BankMigrate_Target` (9 clean target and operational tracking tables).
- **Transformation Algorithm Definitions:** Documented exact field-by-field transformation rules, casing standards, date format parsers (`YYYY-MM-DD` ISO conversion), phone number regex normalizations, email validation regexes, and handling of legacy nulls and default values.

---

### 2. Why It Was Built This Way
- **Architectural Traceability:** Formalizing the mapping document as a version-controlled Markdown asset under `docs/` guarantees that migration transformation code in subsequent milestones (Milestones 7 & 8) directly implements documented specifications rather than implicit assumptions.
- **Declarative Cleaning Contracts:** Defining transformation algorithms prior to coding Python pipeline modules ensures predictable validation logic.

---

### 3. How It Was Built
- **Markdown Specification (`docs/data-mapping.md`):**
  Formatted tables linking legacy column names $\rightarrow$ target column names $\rightarrow$ target SQL data types $\rightarrow$ transformation algorithms $\rightarrow$ input/output transformation examples.
- **Mermaid Diagram Versioning:** Embedded renderable Mermaid `erDiagram` syntax for both legacy and target schemas.

---

### 4. Tech Stack Used in This Step
- **Documentation Standard:** GitHub Flavored Markdown (GFM)
- **Diagramming Engine:** Mermaid JS (`erDiagram`)
- **Version Control:** Git version-controlled asset in `docs/data-mapping.md`

---

## Milestone 5: Build Python Migration Engine Package Skeleton
**Date:** 2026-08-21  
**Status:** COMPLETE  

---

### 1. What Was Built
- **Modular Package Architecture:** Architected and created the complete `migration_engine/` Python package structured into 9 decoupled submodules.
- **Pipeline Orchestrator:** Developed `migration_engine/pipeline.py` implementing `run_pipeline(run_id)` executing the linear pipeline sequence: `extract()` $\rightarrow$ `profile()` $\rightarrow$ `validate()` $\rightarrow$ `transform()` $\rightarrow$ `load()` $\rightarrow$ `reconcile()` $\rightarrow$ `report()`.
- **Skeleton Import Test Suite:** Created `scripts/test_engine_skeleton.py` to verify independent importability and execution of all 9 submodules.

---

### 2. Why It Was Built This Way
- **Package Decoupling over Script Monoliths:** Building a structured Python package (`migration_engine/`) rather than a single monolithic script guarantees that each phase of the migration pipeline operates as an independently callable, testable unit.
- **Strict Linear Pipeline Execution:** Orchestrating pipeline execution through `pipeline.py` ensures that extraction occurs before validation, validation isolates invalid records before transformation, and loading occurs only for valid records.

---

### 3. How It Was Built
- **Module Structure (`migration_engine/`):**
  Implemented submodules in `config/`, `extraction/`, `profiling/`, `validation/`, `transformation/`, `loading/`, `reconciliation/`, `exceptions/`, and `audit/`.
- **Verification Execution (`scripts/test_engine_skeleton.py`):**
  Ran import test suite validating all 9 package submodules. Result: `All 9 submodules imported successfully!`.

---

### 4. Tech Stack Used in This Step
- **Language / Runtime:** Python 3.14.5
- **Data Science / Engineering:** Pandas 3.0.5
- **ORM / DB Toolkit:** SQLAlchemy 2.0.52
- **Database Connectivity:** PyMSSQL 2.3.13
- **Configuration Management:** `python-dotenv` 1.2.3 reading `.env`

---

## Milestone 6: Implement Data Extraction & Profiling Modules
**Date:** 2026-08-21  
**Status:** COMPLETE  

---

### 1. What Was Built
- **Extraction Engine (`migration_engine/extraction/extractor.py`):** Implemented `extract_legacy_data()` and `extract_table(table_name)` functions connecting to `BankMigrate_Legacy` via SQLAlchemy and reading SQL tables into in-memory Pandas DataFrames.
- **Data Profiler (`migration_engine/profiling/profiler.py`):** Implemented `profile_all_tables()` and `profile_dataframe()` computing total row counts, column-level null counts (`df.isnull().sum()`), and duplicate row counts (`df.duplicated().sum()`) per legacy entity.
- **Milestone 6 Verification Runner:** Created [`scripts/run_milestone_6.py`](file:///Users/piyushisinghal/Downloads/BankMigrate/scripts/run_milestone_6.py) to extract and profile all 6 legacy tables.

---

### 2. Why It Was Built This Way
- **DataFrame In-Memory Processing:** Reading legacy tables into Pandas DataFrames provides vectorised, high-speed data manipulation, allowing memory-efficient null inspection and duplicate detection before validation or loading.
- **Proactive Anomaly Profiling:** Generating profiling metrics immediately after extraction provides operational visibility into data quality defects prior to validation enforcement.

---

### 3. How It Was Built
- **Extraction Mechanism:**
  `extract_table(table_name)` reads SQL query output into DataFrame using SQLAlchemy engine.
- **Profiling Metrics Computation:**
  Calculates `total_rows`, `null_counts = df.isnull().sum().to_dict()`, and `duplicate_rows = int(df.duplicated().sum())`.

---

### 4. Tech Stack Used in This Step
- **Language / Runtime:** Python 3.14.5
- **Data Manipulation:** Pandas 3.0.5
- **DB Connector:** SQLAlchemy 2.0.52 + PyMSSQL 2.3.13

---

## Milestone 7: Implement Validation Engine & Rule Catalog Enforcement
**Date:** 2026-08-21  
**Status:** COMPLETE  

---

### 1. What Was Built
- **Validation Engine (`migration_engine/validation/validator.py`):** Built entity validation functions (`validate_customers`, `validate_accounts`, `validate_transactions`, `validate_all_entities`) enforcing the Section 11 rule catalog across all extracted DataFrames.
- **Validation Rule Catalog (`migration_engine/validation/rules.py`):** Implemented stable Rule ID catalog mapping rule IDs (`CUSTOMER_001` through `CUSTOMER_005`, `ACCOUNT_001` through `ACCOUNT_004`, `TXN_001` through `TXN_005`) to error severity levels (`ERROR`, `WARNING`) and human-readable descriptions.
- **Milestone 7 Verification Runner:** Created [`scripts/run_milestone_7.py`](file:///Users/piyushisinghal/Downloads/BankMigrate/scripts/run_milestone_7.py) to run extraction and validation against `BankMigrate_Legacy`.

---

### 2. Why It Was Built This Way
- **Stable Rule Traceability:** Assigning immutable Rule IDs (e.g., `CUSTOMER_001`, `ACCOUNT_002`, `TXN_002`) to every failure condition guarantees that rejected records written to `MigrationExceptions` are audit-ready and reportable via REST APIs.
- **Cascading Referential Integrity Checks:** Validating parent entities before dependent entities ensures that orphan records in child tables are caught by software validation before reaching SQL Server foreign key constraints.

---

### 3. How It Was Built
- **Rule Enforcement Logic (`validator.py`):**
  Implemented validation rules checking missing mandatory fields, duplicate natural keys, email regex matching, DOB strict date parsing, account type enumerations, negative balance checks, and foreign key sets.
- **Verification Execution Output (`scripts/run_milestone_7.py`):**
  Isolated all 9 seeded data-quality defects with exact Rule IDs.

---

### 4. Tech Stack Used in This Step
- **Language / Runtime:** Python 3.14.5
- **Validation Engine & Data Structures:** Pandas 3.0.5, Python Regex (`re`), Datetime (`datetime`)
- **Configuration & Settings:** `migration_engine.config.settings`

---

## Milestone 8: Implement Data Transformation Engine
**Date:** 2026-08-21  
**Status:** COMPLETE  

---

### 1. What Was Built
- **Transformation Engine (`migration_engine/transformation/transformer.py`):** Developed cleaning and mapping modules (`transform_customers`, `transform_accounts`, `transform_transactions`, `transform_all_entities`) applying Section 9 transformation specifications exclusively to valid records.
- **String & Format Normalizer Functions:**
  - `full_name`: Trimmed whitespace, collapsed multiple spaces, and converted to Title Case (`str.title()`).
  - `phone_number`: Stripped non-numeric formatting characters (`+`, `-`, spaces) to yield clean 10-12 digit string (`normalize_phone`).
  - `date_of_birth` / `opened_date` / `start_date`: Converted multi-format strings to ISO standard `YYYY-MM-DD` (`parse_iso_date`).
  - `email`: Trimmed whitespace and converted to lowercase (`str.lower()`).
  - `account_type` / `status` / `transaction_type`: Normalized to UPPERCASE (`SAVINGS`, `ACTIVE`, `DEPOSIT`).
  - Monetary fields (`balance`, `amount`, `loan_amount`): Cast to 2-decimal place numeric values (`round(2)`).
- **Milestone 8 Verification Runner:** Created [`scripts/run_milestone_8.py`](file:///Users/piyushisinghal/Downloads/BankMigrate/scripts/run_milestone_8.py) to execute extraction $\rightarrow$ validation $\rightarrow$ transformation and print transformed entity DataFrames.

---

### 2. Why It Was Built This Way
- **Scope Restriction to Valid Records:** Transformation logic operates strictly on records that passed the validation engine (Milestone 7). Applying transformation logic after validation prevents wasting CPU cycles on invalid or duplicate records destined for the exception store.
- **Standardized Target Schemas:** Output DataFrames produced by `transformer.py` match the target SQL schema column names and data types 1-to-1, ensuring seamless bulk inserts during loading (Milestone 9).

---

### 3. How It Was Built
- **Transformation Algorithm Execution (`transformer.py`):**
  Implemented Title Case, phone digit normalization, ISO date formatting, enumeration uppercasing, and 2-decimal monetary rounding.
- **Verification Execution Output (`scripts/run_milestone_8.py`):**
  Transformed 5 Addresses, 7 Customers, 6 Accounts, 7 Transactions, 2 Loans, 2 Beneficiaries cleanly.

---

### 4. Tech Stack Used in This Step
- **Language / Runtime:** Python 3.14.5
- **Data Engineering:** Pandas 3.0.5
- **Regex & Utilities:** Python `re`, `datetime`

---

## Milestone 9: Implement Target Database Bulk Loading Engine
**Date:** 2026-08-21  
**Status:** COMPLETE  

---

### 1. What Was Built
- **Target Loader Module (`migration_engine/loading/loader.py`):** Built bulk insertion loader (`load_transformed_data`, `load_entity`) persisting clean, transformed DataFrames directly into `BankMigrate_Target` database using SQLAlchemy engine `to_sql`.
- **Foreign Key Dependency Order Control:** Enforced strict relational loading sequence: `Addresses` $\rightarrow$ `Customers` $\rightarrow$ `Accounts` $\rightarrow$ `Transactions` $\rightarrow$ `Loans` $\rightarrow$ `Beneficiaries`.
- **Target Table Truncation (`clear_target_tables`):** Added capability to clear target tables in reverse foreign key order before fresh pipeline execution.
- **Milestone 9 Verification Runner:** Created [`scripts/run_milestone_9.py`](file:///Users/piyushisinghal/Downloads/BankMigrate/scripts/run_milestone_9.py) executing extraction $\rightarrow$ validation $\rightarrow$ transformation $\rightarrow$ target loading, followed by direct T-SQL row count verification queries against SQL Server.

---

### 2. Why It Was Built This Way
- **Foreign Key Safe Execution:** Ordering target loads by entity dependencies prevents SQL Server foreign key violation errors.
- **Transactional Bulk Appending:** Utilizing SQLAlchemy `to_sql(..., if_exists='append', index=False)` provides high-throughput batch insertion into target tables while respecting target database constraints.

---

### 3. How It Was Built
- **Relational Loading Implementation (`loader.py`):**
  Loops through `LOAD_ORDER` list, calling `df.to_sql(name=table_name, con=engine, if_exists="append", index=False)`.
- **SQL Server Verification (`scripts/run_milestone_9.py`):**
  Queried `BankMigrate_Target` via PyMSSQL cursor: 29 clean rows loaded into target database.

---

### 4. Tech Stack Used in This Step
- **Database Engine:** Microsoft SQL Server (Azure SQL Edge container `mcr.microsoft.com/azure-sql-edge:latest`)
- **Language / Runtime:** Python 3.14.5
- **ORM / DB Engine:** SQLAlchemy 2.0.52
- **Database Driver:** PyMSSQL 2.3.13
- **Data Engineering:** Pandas 3.0.5

---

## Milestone 10: Build T-SQL Stored Procedure Layer
**Date:** 2026-08-21  
**Status:** COMPLETE  

---

### 1. What Was Built
- **Enterprise T-SQL Stored Procedure Library:** Implemented 6 core database stored procedures in `BankMigrate_Target` (defined in `scripts/sql/04_create_stored_procedures.sql`):
  1. `sp_detect_duplicates`: Performs window-function duplicate detection (`ROW_NUMBER() OVER (PARTITION BY ...)`).
  2. `sp_validate_customers`: Runs `CUSTOMER_*` validation checks using CTEs, temp tables (`#CustExceptions`), and `TRY...CATCH` blocks.
  3. `sp_validate_accounts`: Runs `ACCOUNT_*` validation checks against staged legacy data.
  4. `sp_validate_transactions`: Runs `TXN_*` validation checks.
  5. `sp_reconcile_migration`: Compares source vs target record counts and calculates monetary transaction totals (`SourceTxnSum = TargetTxnSum + RejectedTxnSum`).
  6. `sp_generate_migration_summary`: Produces run-level summary report joining `MigrationRuns`, `MigrationExceptions`, and `MigrationAudit`.
- **Deployment & Verification Script:** Created `scripts/create_stored_procedures.py` to deploy and verify all 6 procedures in SQL Server.

---

### 2. Why It Was Built This Way
- **Database-Native Set Processing:** Implementing validation and duplicate detection in T-SQL stored procedures demonstrates advanced database capabilities (CTEs, Window Functions, Temp Tables, `TRY...CATCH`, explicit `BEGIN TRAN / COMMIT / ROLLBACK` transactions).
- **Dual Layer Architecture:** Demonstrates both Python application-level validation and SQL Server database-level stored procedure validation.

---

### 3. How It Was Built
- **T-SQL Scripting (`scripts/sql/04_create_stored_procedures.sql`):**
  Implemented window-function duplicate detection, temp table exception staging, JSON string snapshotting, and transaction control.
- **Deployment Verification (`scripts/create_stored_procedures.py`):**
  Queried `INFORMATION_SCHEMA.ROUTINES`: All 6 stored procedures verified as DEPLOYED.

---

### 4. Tech Stack Used in This Step
- **Database Engine:** Microsoft SQL Server (Azure SQL Edge container `mcr.microsoft.com/azure-sql-edge:latest`)
- **SQL Dialect:** T-SQL (Window Functions, CTEs, Temp Tables, `TRY...CATCH`, Transactions, JSON Path)
- **Database Driver:** PyMSSQL 2.3.13
- **Language / Runtime:** Python 3.14.5

---

## Milestone 11: Implement Exception Store & Exception Handling Layer
**Date:** 2026-08-21  
**Status:** COMPLETE  

---

### 1. What Was Built
- **Exception Handler Module (`migration_engine/exceptions/handler.py`):** Developed `record_exceptions(run_id, exceptions_list)` and `get_run_exceptions(run_id)` connecting to `BankMigrate_Target`.
- **Exception Store Persistence:** Writes every rejected record into `MigrationExceptions` table, persisting `run_id`, `entity_type`, `record_id`, `rule_id`, `severity`, `error_message`, `source_data`, and `status`.
- **Milestone 11 Verification Runner:** Integrated into `scripts/run_milestones_10_11_12.py`.

---

### 2. Why It Was Built This Way
- **Zero Silent Data Loss:** Isolating rejected records into a structured SQL exception store ensures that bad legacy data never silently disappears.
- **Auditability & Traceability:** Preserving `source_data` as a JSON string inside `MigrationExceptions` provides an immutable audit trail of the original raw record.

---

### 3. How It Was Built
- **Parameterized SQL Persistence (`handler.py`):**
  Uses PyMSSQL cursor executing parameterized bulk inserts into `MigrationExceptions`.
- **Verification Execution Output (`scripts/run_milestones_10_11_12.py`):**
  Persisted and queried 9 exception records from SQL Server `MigrationExceptions` table for run `RUN-TEST-M10-M12`.

---

### 4. Tech Stack Used in This Step
- **Database Engine:** Microsoft SQL Server
- **Language / Runtime:** Python 3.14.5
- **Database Driver:** PyMSSQL 2.3.13
- **Data Serialization:** Python `json`

---

## Milestone 12: Implement Automated Reconciliation Engine
**Date:** 2026-08-21  
**Status:** COMPLETE  

---

### 1. What Was Built
- **Reconciliation Engine (`migration_engine/reconciliation/reconciler.py`):** Built `reconcile_run(run_id, summary_counts)` executing automated mathematical and database reconciliation checks for every migration run.
- **Record Count Reconciliation Math:**
  Verifies $\text{Source Records} = \text{Validated Records} + \text{Rejected Records}$ and $\text{Validated Records} = \text{Loaded Records}$.
- **Monetary Amount Reconciliation:** Invokes T-SQL stored procedure `sp_reconcile_migration` in SQL Server to compute monetary balance across financial transaction tables: $\text{Source Transaction Amount} = \text{Target Transaction Amount} + \text{Rejected Transaction Amount}$.
- **Milestone 12 Verification Runner:** Integrated into [`scripts/run_milestones_10_11_12.py`](file:///Users/piyushisinghal/Downloads/BankMigrate/scripts/run_milestones_10_11_12.py).

---

### 2. Why It Was Built This Way
- **Automated Verification over Manual Spot-Checks:** Running automated mathematical reconciliation at the end of every migration run proves that no records or dollar amounts were lost or unaccounted for during processing.
- **Financial Audit Rigor:** Reconciling dollar amounts (Source Txn Sum = Target Txn Sum + Rejected Txn Sum) is mandatory in banking to guarantee financial balance integrity.

---

### 3. How It Was Built
- **Reconciliation Algorithm (`reconciler.py`):**
  Evaluates count balance and calls `cursor.callproc("sp_reconcile_migration", (run_id,))`.
- **Verification Execution Output (`scripts/run_milestones_10_11_12.py`):**
  Verified $38 = 29 + 9 \rightarrow$ `BALANCED` ✅.

---

### 4. Tech Stack Used in This Step
- **Database Engine:** Microsoft SQL Server
- **SQL Dialect:** T-SQL Stored Procedure `sp_reconcile_migration`
- **Language / Runtime:** Python 3.14.5
- **Database Driver:** PyMSSQL 2.3.13

---

## Milestone 13: Implement Migration Run Tracking & Audit Logging
**Date:** 2026-08-21  
**Status:** COMPLETE  

---

### 1. What Was Built
- **Run Tracking Module (`migration_engine/audit/logger.py`):** Implemented `create_migration_run(run_id)` and `update_migration_run(run_id, counts, status)` creating and updating lifecycle tracking records in `MigrationRuns`.
- **Audit Logging Module:** Implemented `log_audit_event()` and `log_audit_batch()` writing an append-only audit trail for every loaded (`INSERT`) and rejected (`REJECT`) record into `MigrationAudit`.
- **Milestone 13 Verification Runner:** Created [`scripts/run_milestones_13_14_15.py`](file:///Users/piyushisinghal/Downloads/BankMigrate/scripts/run_milestones_13_14_15.py) to run the migration pipeline and verify audit entries directly in SQL Server.

---

### 2. Why It Was Built This Way
- **Operational Visibility:** Wrapping every migration run inside `MigrationRuns` provides real-time state tracking (`IN_PROGRESS`, `COMPLETED`, `COMPLETED_WITH_EXCEPTIONS`) and stage-by-stage record counts.
- **Append-Only Audit Trail:** Logging every atomic DML event into `MigrationAudit` provides complete compliance traceability required by financial auditors.

---

### 3. How It Was Built
- **Lifecycle Tracking (`logger.py`):**
  - `create_migration_run`: Idempotently inserts/resets `MigrationRuns` row with `status = 'IN_PROGRESS'`.
  - `log_audit_batch`: Bulk inserts atomic operation rows into `MigrationAudit` (`INSERT` / `REJECT`).
  - `update_migration_run`: Finalizes run metrics and sets completed timestamp and run status.
- **Verification Output (`scripts/run_milestones_13_14_15.py`):**
  Verified `MigrationRuns` record (`RUN-TEST-M13-M15`, status: `COMPLETED_WITH_EXCEPTIONS`) and 74 `MigrationAudit` entries in SQL Server.

---

### 4. Tech Stack Used in This Step
- **Database Engine:** Microsoft SQL Server
- **Language / Runtime:** Python 3.14.5
- **Database Driver:** PyMSSQL 2.3.13

---

## Milestone 14: Build ASP.NET Core REST API Layer
**Date:** 2026-08-21  
**Status:** COMPLETE  

---

### 1. What Was Built
- **ASP.NET Core 8 Web API Project:** Built and compiled C# Web API project [`api/BankMigrate.Api.csproj`](file:///Users/piyushisinghal/Downloads/BankMigrate/api/BankMigrate.Api.csproj) providing RESTful orchestration and reporting endpoints.
- **REST Controller (`api/Controllers/MigrationController.cs`):** Exposed all 6 required REST endpoints matching PDF Section 17:
  1. `POST /api/migrations`: Starts a new migration run (triggers Python engine).
  2. `GET /api/migrations`: Lists all past and current migration runs from `MigrationRuns`.
  3. `GET /api/migrations/{runId}`: Gets detailed status and record counts for one run.
  4. `GET /api/migrations/{runId}/exceptions`: Lists all rejected records for a run from `MigrationExceptions`.
  5. `GET /api/migrations/{runId}/reconciliation`: Returns reconciliation report for a run (invoking `sp_reconcile_migration`).
  6. `POST /api/migrations/{runId}/retry`: Retries a failed or partially completed run.
- **Services & Models Layer (`api/Services/`, `api/Models/`):**
  - `MigrationService.cs`: Triggers the Python pipeline process via `System.Diagnostics.Process`.
  - `ReportingService.cs`: Queries `BankMigrate_Target` using Dapper and `Microsoft.Data.SqlClient`.
  - `MigrationModels.cs`: DTO models (`MigrationRunDto`, `ExceptionDto`, `ReconciliationReportDto`).

---

### 2. Why It Was Built This Way
- **Genuine API Orchestration & Reporting:** Decouples REST HTTP management from batch Python processing. The API acts as the administrative control plane, exposing run status, exceptions, and reconciliation reports without embedding heavy data processing inside web server threads.
- **High-Performance SQL Querying with Dapper:** Uses Dapper micro-ORM for lightweight, high-speed execution of parameterized SQL queries against `MigrationRuns` and `MigrationExceptions`.

---

### 3. How It Was Built
- **C# Controller & Service Architecture:**
  Constructed `MigrationController` delegating orchestration to `IMigrationService` and database reporting to `IReportingService`.
- **Build & Verification (`dotnet build`):**
  Built `api/BankMigrate.Api.csproj` targeting .NET 8.0. Result: `Build succeeded. 0 Warning(s), 0 Error(s)`.

---

### 4. Tech Stack Used in This Step
- **Framework / Language:** .NET 8.0 C# (ASP.NET Core Web API)
- **Data Access:** Dapper 2.1.79 + Microsoft.Data.SqlClient 7.0.2
- **OpenAPI:** Swashbuckle / SwaggerGen

---

## Milestone 15: Add Automated Scheduler Engine
**Date:** 2026-08-21  
**Status:** COMPLETE  

---

### 1. What Was Built
- **Automated Scheduler Package (`scheduler/migration_scheduler.py`):** Created `MigrationScheduler` module utilizing `APScheduler` (BackgroundScheduler) to execute recurring migration jobs on a cron-style interval.
- **Scheduler Runner Script:** Built `scripts/start_scheduler.py` allowing operators to launch the background automated scheduler from CLI.
- **Milestone 15 Verification Runner:** Integrated into [`scripts/run_milestones_13_14_15.py`](file:///Users/piyushisinghal/Downloads/BankMigrate/scripts/run_milestones_13_14_15.py) to trigger background scheduled migration execution.

---

### 2. Why It Was Built This Way
- **Automated vs Manual Execution:** Real production banking migration platforms run on automated schedules (e.g. nightly batch windows at 02:00 AM) rather than requiring manual developer triggers every time.
- **Robust Background Scheduling:** Utilizing `APScheduler` provides interval and cron triggers that execute `run_pipeline()` asynchronously, logging status and handling exceptions gracefully.

---

### 3. How It Was Built
- **Scheduler Implementation (`migration_scheduler.py`):**
  Uses `BackgroundScheduler.add_job` with `IntervalTrigger(minutes=interval_minutes)`.
- **Verification Execution Output (`scripts/run_milestones_13_14_15.py`):**
  Triggered automated scheduled run `SCHED-RUN-20260821-033922`. Verified completion status: `COMPLETED_WITH_EXCEPTIONS`.

---

### 4. Tech Stack Used in This Step
- **Language / Runtime:** Python 3.14.5
- **Scheduling Library:** APScheduler 3.11.3
- **Configuration & Core Engine:** `migration_engine.pipeline`

---

## Milestone 16: Implement Failure Simulation & Recovery Engine
**Date:** 2026-08-21  
**Status:** COMPLETE  

---

### 1. What Was Built
- **Failure Simulator Module (`migration_engine/exceptions/simulator.py`):** Built failure injection engine supporting `NETWORK_DROP`, `LOCKED_TABLE`, and `DIRTY_INPUT` failure flags.
- **Pipeline Exception Catching & FAILED State Transitions:** Updated `migration_engine/pipeline.py` to intercept runtime failures, transition `MigrationRuns.status` to `'FAILED'`, and log `PIPELINE_FAILURE` events in `MigrationAudit`.
- **Automated Retry & Recovery Engine:** Added retry capability clearing intermediate dirty states, re-extracting legacy data, re-validating, transforming, bulk loading clean records, and restoring target database consistency.
- **Milestone 16 Verification Runner:** Created [`scripts/run_milestones_16_17.py`](file:///Users/piyushisinghal/Downloads/BankMigrate/scripts/run_milestones_16_17.py) testing failure injection and retry recovery.

---

### 2. Why It Was Built This Way
- **Resilience under Adverse Conditions:** Financial data pipelines must handle transient network drops, database table locks, and corrupted data batches gracefully without corrupting target database states or losing run state tracking.
- **Deterministic Failure Testing:** Injecting explicit failure modes (`NETWORK_DROP`, `LOCKED_TABLE`) proves that the pipeline's exception handler and retry mechanisms operate correctly under real-world disaster recovery scenarios.

---

### 3. How It Was Built
- **Failure Injection Execution (`simulator.py`):**
  Hooks into pipeline stages (`extraction`, `loading`, `validation`) raising `MigrationFailureException`.
- **Verification Execution Output (`scripts/run_milestones_16_17.py`):**
  - Injected `NETWORK_DROP` into `RUN-FAIL-NET` $\rightarrow$ status set to `FAILED` in SQL Server ✅.
  - Injected `LOCKED_TABLE` into `RUN-FAIL-LOCK` $\rightarrow$ status set to `FAILED` in SQL Server ✅.
  - Triggered Retry recovery on `RUN-FAIL-NET` $\rightarrow$ status recovered to `COMPLETED_WITH_EXCEPTIONS`, loaded 29 clean target rows ✅.

---

### 4. Tech Stack Used in This Step
- **Database Engine:** Microsoft SQL Server
- **Language / Runtime:** Python 3.14.5
- **Exception Framework:** Python custom exceptions, `pymssql` transactional rollback

---

## Milestone 17: Apply Security Hardening & PII Protection
**Date:** 2026-08-21  
**Status:** COMPLETE  

---

### 1. What Was Built
- **Least-Privilege Database Role Script (`scripts/sql/05_security_hardening.sql`):** Created T-SQL script provisioning `bankmigrate_app_role` in SQL Server with `SELECT`, `INSERT`, `UPDATE`, `EXECUTE` privileges on `BankMigrate_Legacy` and `BankMigrate_Target`, denying `ALTER` or sysadmin privileges.
- **SQL Parameterization Audit:** Verified 100% parameterization across all Python database queries (`pymssql` `%s`, Dapper `@Param`), ensuring 0 inline string concatenations.
- **Secrets Management:** Verified all credentials read dynamically from environment variables / `.env` (`python-dotenv` in Python, `IConfiguration` in C#).
- **PII Masking & Sanitization Module (`migration_engine/validation/sanitizer.py`):** Implemented `mask_email`, `mask_phone`, and `mask_dob` helper functions to sanitize sensitive customer banking data in diagnostic log messages.

---

### 2. Why It Was Built This Way
- **Least-Privilege Database Principle:** Application engines should never connect to enterprise banking databases using `sa` or `sysadmin` credentials in production. Provisioning a restricted role (`bankmigrate_app_role`) enforces schema isolation and prevents unauthorized DDL drops.
- **SQL Injection Prevention:** Parameterizing 100% of queries prevents SQL injection vulnerabilities.
- **Data Privacy Compliance (GDPR / GLBA):** Masking customer PII in log files guarantees compliance with financial data privacy regulations.

---

### 3. How It Was Built
- **T-SQL Role Creation (`05_security_hardening.sql`):**
  ```sql
  CREATE ROLE bankmigrate_app_role;
  GRANT SELECT, INSERT, UPDATE, DELETE ON SCHEMA::dbo TO bankmigrate_app_role;
  GRANT EXECUTE ON SCHEMA::dbo TO bankmigrate_app_role;
  DENY ALTER TO bankmigrate_app_role;
  ```
- **PII Sanitization Logic (`sanitizer.py`):**
  - `mask_email('john.smith@gmail.com')` $\rightarrow$ `'j********h@gmail.com'`
  - `mask_phone('+91-98765-43210')` $\rightarrow$ `'********3210'`
  - `mask_dob('1985-05-15')` $\rightarrow$ `'XXXX-XX-15'`

---

### 4. Tech Stack Used in This Step
- **Database Security:** Microsoft SQL Server Database Roles & Schema Permissions
- **Security Engineering:** T-SQL DCL (`GRANT`, `DENY`), Python `re` Regex
- **Language / Runtime:** Python 3.14.5, C# .NET 8.0
