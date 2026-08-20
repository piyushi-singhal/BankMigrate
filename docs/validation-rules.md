# Validation Engine Rules Specification

## Overview
Every data quality check in BankMigrate is identified by a unique, stable Rule ID. When a record fails a validation check, the engine isolates the record and writes a structured entry to `MigrationExceptions` with the exact Rule ID, severity level, error message, and source data snapshot.

---

## Validation Rule Catalog

### Customer Entity Rules

| Rule ID | Rule Name | Description / Condition | Severity | Action on Failure |
| :--- | :--- | :--- | :--- | :--- |
| `CUSTOMER_001` | Customer ID Required | `customer_id` IS NULL OR TRIM(`customer_id`) == '' | ERROR | Reject record; write to `MigrationExceptions` |
| `CUSTOMER_002` | Duplicate Customer | Multiple customer records with identical natural key / normalized name & DOB | ERROR | Reject duplicate records; log to exception store |
| `CUSTOMER_003` | Invalid Phone Number | Phone number contains non-numeric chars (outside formatting) or fails length check (10-15 digits) | WARNING / ERROR | Standardize if fixable, reject if unparseable |
| `CUSTOMER_004` | Invalid Email Format | Email does not match regex standard `^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$` | ERROR | Reject record |
| `CUSTOMER_005` | Invalid Date of Birth | `dob` is malformed date string (e.g. `31/02/1999`) or date in future or age > 120 | ERROR | Reject record |

### Account Entity Rules

| Rule ID | Rule Name | Description / Condition | Severity | Action on Failure |
| :--- | :--- | :--- | :--- | :--- |
| `ACCOUNT_001` | Account ID Required | `account_id` IS NULL OR TRIM(`account_id`) == '' | ERROR | Reject record |
| `ACCOUNT_002` | Referenced Customer Exists | `customer_id` must exist in target `Customers` table (referential integrity) | ERROR | Reject record |
| `ACCOUNT_003` | Valid Account Type | `account_type` MUST BE IN (`SAVINGS`, `CHECKING`, `CURRENT`, `LOAN`) | ERROR | Reject record |
| `ACCOUNT_004` | Valid Account Balance | `balance` MUST BE $\ge 0$ for non-credit accounts (`SAVINGS`, `CHECKING`) | ERROR | Reject record |

### Transaction Entity Rules

| Rule ID | Rule Name | Description / Condition | Severity | Action on Failure |
| :--- | :--- | :--- | :--- | :--- |
| `TXN_001` | Transaction ID Required | `transaction_id` IS NULL OR TRIM(`transaction_id`) == '' | ERROR | Reject record |
| `TXN_002` | Referenced Account Exists | `account_id` must exist in target `Accounts` table (e.g. catches `A999999`) | ERROR | Reject record; preserve source record snapshot |
| `TXN_003` | Valid Transaction Amount | `amount` MUST BE $> 0$ (non-zero positive decimal) | ERROR | Reject record |
| `TXN_004` | Valid Transaction Date | `transaction_date` must be valid timestamp and NOT in future | ERROR | Reject record |
| `TXN_005` | Duplicate Transaction | Exact duplicate `transaction_id` or identical `(account_id, amount, transaction_date)` | ERROR | Reject duplicate instance |

---

## Example Exception Payload
```json
{
  "exception_id": 10291,
  "run_id": "RUN-20260821-001",
  "entity_type": "Transaction",
  "record_id": "TXN-89231",
  "rule_id": "TXN_002",
  "severity": "ERROR",
  "error_message": "Referenced account A999999 does not exist in target Accounts table",
  "source_data": "{\"transaction_id\": \"TXN-89231\", \"account_id\": \"A999999\", \"amount\": 250.00, \"transaction_date\": \"2026-08-20 14:20:00\"}",
  "created_at": "2026-08-21T02:35:00Z",
  "status": "OPEN"
}
```
