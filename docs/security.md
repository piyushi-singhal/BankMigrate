# Security & Privacy Guidelines

## Baseline Security Principles
BankMigrate strictly adheres to enterprise data protection and application security standards:

> [!IMPORTANT]  
> **Synthetic Data Declaration:** All banking records, customer names, accounts, transaction amounts, and addresses used in this project are 100% synthetic. No actual customer, account, or financial data is stored or processed.

---

## Security Controls Checklist

- [x] **Credential Management:** Database passwords and connection parameters are loaded exclusively from `.env` files / environment variables and never hardcoded in source files.
- [x] **Source Control Exclusion:** The `.env` file is explicitly ignored in `.gitignore`.
- [x] **SQL Injection Prevention:** All SQL queries in Python and T-SQL stored procedures use parameterized queries and ORM abstractions (SQLAlchemy / PyMSSQL parameterized execution). No raw string concatenation is permitted for SQL construction.
- [x] **Least Privilege Access:** Database connections utilize restricted database users with permissions scoped strictly to DDL/DML on `BankMigrate_Legacy` and `BankMigrate_Target`.
- [x] **Audit Logging:** All data-modifying events (inserts, updates, exception logging) write structured records to `MigrationAudit`.
- [x] **API Input Validation:** API endpoints validate path parameters, request bodies, and run identifiers.
