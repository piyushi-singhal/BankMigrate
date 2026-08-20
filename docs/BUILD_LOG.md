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
  ```python
  def extract_table(table_name: str) -> pd.DataFrame:
      engine = get_legacy_engine()
      return pd.read_sql(f"SELECT * FROM {table_name};", con=engine)
  ```
- **Profiling Metrics Computation:**
  Calculates `total_rows`, `null_counts = df.isnull().sum().to_dict()`, and `duplicate_rows = int(df.duplicated().sum())`.
- **Verification Output (`scripts/run_milestone_6.py`):**
  - Extracted 6 tables total.
  - `Customers_Legacy`: 11 total rows, 1 null `customer_id` detected.
  - `Transactions_Legacy`: 10 total rows, 1 duplicate row detected (`TXN-1005`).

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
- **Relational Dependency Order Validation:** Structured validation to validate parent entities (`Customers`) first, collecting valid customer IDs to enforce referential integrity checks on dependent entities (`Accounts`), and using valid account IDs for `Transactions` validation.
- **Milestone 7 Verification Runner:** Created [`scripts/run_milestone_7.py`](file:///Users/piyushisinghal/Downloads/BankMigrate/scripts/run_milestone_7.py) to run extraction and validation against `BankMigrate_Legacy`.

---

### 2. Why It Was Built This Way
- **Stable Rule Traceability:** Assigning immutable Rule IDs (e.g., `CUSTOMER_001`, `ACCOUNT_002`, `TXN_002`) to every failure condition guarantees that rejected records written to `MigrationExceptions` are audit-ready and reportable via REST APIs.
- **Cascading Referential Integrity Checks:** Validating parent entities before dependent entities ensures that orphan records in child tables (e.g. account `A010` referencing nonexistent customer `C999`, or transaction `TXN-89231` referencing nonexistent account `A999999`) are caught by software validation before reaching SQL Server foreign key constraints.
- **Data Preservation on Rejection:** When a record fails validation, the record is isolated into the exceptions list alongside a full JSON snapshot of `source_data`, ensuring zero silent data loss.

---

### 3. How It Was Built
- **Rule Enforcement Logic (`validator.py`):**
  - `CUSTOMER_001`: Checks `pd.isna(cust_id)`. Catches record `Jane Doe`.
  - `CUSTOMER_002`: Checks natural key `(name.lower(), dob)` and duplicate ID. Catches duplicate record `C019`.
  - `CUSTOMER_004`: Regex `^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$`. Catches `charlie_brown_at_domain.com`.
  - `CUSTOMER_005`: Strict DOB parsing. Catches invalid date `31/02/1999`.
  - `ACCOUNT_002`: Foreign key check `cust_id in valid_customer_ids`. Catches `A010` (referencing `C999`).
  - `ACCOUNT_004`: Negative balance check on Savings/Checking. Catches `A004` (balance `-500.00`).
  - `TXN_002`: Foreign key check `acct_id in valid_account_ids`. Catches orphan transaction `TXN-89231` (referencing `A999999`).
  - `TXN_003`: Negative amount check `amount <= 0`. Catches `TXN-1008` (amount `-100.00`).
  - `TXN_005`: Duplicate transaction ID check. Catches duplicate `TXN-1005`.
- **Verification Execution Output (`scripts/run_milestone_7.py`):**
  ```text
  --- VALIDATION RESULTS SUMMARY ---
    • Entity 'Addresses': 5 original records -> 5 VALID passed.
    • Entity 'Customers': 11 original records -> 7 VALID passed.
    • Entity 'Accounts': 8 original records -> 6 VALID passed.
    • Entity 'Transactions': 10 original records -> 7 VALID passed.
    • Entity 'Loans': 2 original records -> 2 VALID passed.
    • Entity 'Beneficiaries': 2 original records -> 2 VALID passed.

  Total Exceptions Isolated: 9 (Matching all 9 seeded defects!)
  ```

---

### 4. Tech Stack Used in This Step
- **Language / Runtime:** Python 3.14.5
- **Validation Engine & Data Structures:** Pandas 3.0.5, Python Regex (`re`), Datetime (`datetime`)
- **Configuration & Settings:** `migration_engine.config.settings`
