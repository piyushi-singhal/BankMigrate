import re
import json
import pandas as pd
from datetime import datetime
from .rules import VALIDATION_RULES

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
VALID_ACCOUNT_TYPES = {"SAVINGS", "CHECKING", "CURRENT", "LOAN"}

def parse_date_strict(date_str: str) -> bool:
    """Returns True if date_str is valid date format YYYY-MM-DD or DD/MM/YYYY, False otherwise."""
    if not date_str or pd.isna(date_str):
        return False
    s = str(date_str).strip()
    try:
        if "/" in s:
            datetime.strptime(s, "%d/%m/%Y")
        else:
            datetime.strptime(s[:10], "%Y-%m-%d")
        return True
    except ValueError:
        return False

def validate_customers(df: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    """
    Applies rules CUSTOMER_001 through CUSTOMER_005 to Customers_Legacy.
    Returns (valid_df, exceptions_list).
    """
    valid_rows = []
    exceptions = []
    seen_customer_ids = set()
    seen_natural_keys = set()

    for _, row in df.iterrows():
        cust_id = row.get("customer_id")
        cust_name = str(row.get("customer_name") or "").strip()
        dob = str(row.get("dob") or "").strip()
        phone = str(row.get("phone") or "").strip()
        email = str(row.get("email") or "").strip()

        row_errors = []
        source_snapshot = json.dumps(row.to_dict(), default=str)

        # CUSTOMER_001: Missing Customer ID
        if pd.isna(cust_id) or not str(cust_id).strip():
            row_errors.append({
                "rule_id": "CUSTOMER_001",
                "entity_type": "Customer",
                "record_id": None,
                "severity": "ERROR",
                "error_message": "Customer ID is required and cannot be NULL or empty.",
                "source_data": source_snapshot
            })

        # CUSTOMER_002: Duplicate customer (ID or Natural Key name+DOB)
        cust_id_str = str(cust_id).strip() if cust_id is not None else None
        natural_key = (cust_name.lower(), dob)

        if cust_id_str and (cust_id_str in seen_customer_ids or natural_key in seen_natural_keys):
            row_errors.append({
                "rule_id": "CUSTOMER_002",
                "entity_type": "Customer",
                "record_id": cust_id_str,
                "severity": "ERROR",
                "error_message": f"Duplicate customer record detected for ID '{cust_id_str}' or Name '{cust_name}' / DOB '{dob}'.",
                "source_data": source_snapshot
            })
        else:
            if cust_id_str:
                seen_customer_ids.add(cust_id_str)
                if cust_name and dob:
                    seen_natural_keys.add(natural_key)

        # CUSTOMER_004: Invalid Email Format
        if email and not EMAIL_REGEX.match(email):
            row_errors.append({
                "rule_id": "CUSTOMER_004",
                "entity_type": "Customer",
                "record_id": cust_id_str,
                "severity": "ERROR",
                "error_message": f"Invalid email format: '{email}'. Must match user@domain.com standard.",
                "source_data": source_snapshot
            })

        # CUSTOMER_005: Invalid Date of Birth
        if dob and not parse_date_strict(dob):
            row_errors.append({
                "rule_id": "CUSTOMER_005",
                "entity_type": "Customer",
                "record_id": cust_id_str,
                "severity": "ERROR",
                "error_message": f"Invalid date of birth: '{dob}'. Date does not exist or format is unsupported.",
                "source_data": source_snapshot
            })

        # CUSTOMER_003: Invalid Phone Format check (Warning level check)
        digits_phone = re.sub(r"\D", "", phone)
        if phone and (len(digits_phone) < 7 or len(digits_phone) > 15):
            row_errors.append({
                "rule_id": "CUSTOMER_003",
                "entity_type": "Customer",
                "record_id": cust_id_str,
                "severity": "WARNING",
                "error_message": f"Non-standard phone number format: '{phone}'.",
                "source_data": source_snapshot
            })

        # Separate rejections (ERROR level) from valid rows
        fatal_errors = [e for e in row_errors if e["severity"] == "ERROR"]
        if fatal_errors:
            exceptions.extend(row_errors)
        else:
            if row_errors:
                exceptions.extend(row_errors) # Log warnings but keep record valid
            valid_rows.append(row)

    valid_df = pd.DataFrame(valid_rows) if valid_rows else pd.DataFrame(columns=df.columns)
    return valid_df, exceptions

def validate_accounts(df: pd.DataFrame, valid_customer_ids: set) -> tuple[pd.DataFrame, list[dict]]:
    """
    Applies rules ACCOUNT_001 through ACCOUNT_004 to Accounts_Legacy.
    """
    valid_rows = []
    exceptions = []

    for _, row in df.iterrows():
        acct_id = row.get("account_id")
        cust_id = row.get("customer_id")
        acct_type = str(row.get("account_type") or "").strip().upper()
        balance = row.get("balance")
        opened_date = str(row.get("opened_date") or "").strip()

        row_errors = []
        source_snapshot = json.dumps(row.to_dict(), default=str)
        acct_id_str = str(acct_id).strip() if acct_id is not None else None
        cust_id_str = str(cust_id).strip() if cust_id is not None else None

        # ACCOUNT_001: Missing Account ID
        if pd.isna(acct_id) or not acct_id_str:
            row_errors.append({
                "rule_id": "ACCOUNT_001",
                "entity_type": "Account",
                "record_id": None,
                "severity": "ERROR",
                "error_message": "Account ID is required and cannot be NULL or empty.",
                "source_data": source_snapshot
            })

        # ACCOUNT_002: Customer FK Validation
        if not cust_id_str or cust_id_str not in valid_customer_ids:
            row_errors.append({
                "rule_id": "ACCOUNT_002",
                "entity_type": "Account",
                "record_id": acct_id_str,
                "severity": "ERROR",
                "error_message": f"Referenced customer '{cust_id_str}' does not exist in target Customers table.",
                "source_data": source_snapshot
            })

        # ACCOUNT_003: Valid Account Type
        if acct_type not in VALID_ACCOUNT_TYPES:
            row_errors.append({
                "rule_id": "ACCOUNT_003",
                "entity_type": "Account",
                "record_id": acct_id_str,
                "severity": "ERROR",
                "error_message": f"Invalid account type '{acct_type}'. Must be SAVINGS, CHECKING, CURRENT, or LOAN.",
                "source_data": source_snapshot
            })

        # ACCOUNT_004: Invalid Negative Balance
        if acct_type in ("SAVINGS", "CHECKING") and balance is not None and float(balance) < 0:
            row_errors.append({
                "rule_id": "ACCOUNT_004",
                "entity_type": "Account",
                "record_id": acct_id_str,
                "severity": "ERROR",
                "error_message": f"Invalid negative balance ({balance}) on {acct_type} account.",
                "source_data": source_snapshot
            })

        fatal_errors = [e for e in row_errors if e["severity"] == "ERROR"]
        if fatal_errors:
            exceptions.extend(row_errors)
        else:
            valid_rows.append(row)

    valid_df = pd.DataFrame(valid_rows) if valid_rows else pd.DataFrame(columns=df.columns)
    return valid_df, exceptions

def validate_transactions(df: pd.DataFrame, valid_account_ids: set) -> tuple[pd.DataFrame, list[dict]]:
    """
    Applies rules TXN_001 through TXN_005 to Transactions_Legacy.
    """
    valid_rows = []
    exceptions = []
    seen_txn_ids = set()

    for _, row in df.iterrows():
        txn_id = row.get("transaction_id")
        acct_id = row.get("account_id")
        amount = row.get("amount")
        txn_date = str(row.get("transaction_date") or "").strip()

        row_errors = []
        source_snapshot = json.dumps(row.to_dict(), default=str)
        txn_id_str = str(txn_id).strip() if txn_id is not None else None
        acct_id_str = str(acct_id).strip() if acct_id is not None else None

        # TXN_001: Missing Transaction ID
        if pd.isna(txn_id) or not txn_id_str:
            row_errors.append({
                "rule_id": "TXN_001",
                "entity_type": "Transaction",
                "record_id": None,
                "severity": "ERROR",
                "error_message": "Transaction ID is required.",
                "source_data": source_snapshot
            })

        # TXN_005: Duplicate Transaction
        if txn_id_str and txn_id_str in seen_txn_ids:
            row_errors.append({
                "rule_id": "TXN_005",
                "entity_type": "Transaction",
                "record_id": txn_id_str,
                "severity": "ERROR",
                "error_message": f"Duplicate transaction ID '{txn_id_str}' detected.",
                "source_data": source_snapshot
            })
        else:
            if txn_id_str:
                seen_txn_ids.add(txn_id_str)

        # TXN_002: Account FK Validation
        if not acct_id_str or acct_id_str not in valid_account_ids:
            row_errors.append({
                "rule_id": "TXN_002",
                "entity_type": "Transaction",
                "record_id": txn_id_str,
                "severity": "ERROR",
                "error_message": f"Referenced account '{acct_id_str}' does not exist in target Accounts table.",
                "source_data": source_snapshot
            })

        # TXN_003: Invalid Transaction Amount (Must be > 0)
        if amount is not None and float(amount) <= 0:
            row_errors.append({
                "rule_id": "TXN_003",
                "entity_type": "Transaction",
                "record_id": txn_id_str,
                "severity": "ERROR",
                "error_message": f"Invalid transaction amount: {amount}. Must be a positive decimal.",
                "source_data": source_snapshot
            })

        # TXN_004: Invalid Transaction Date
        if txn_date and not parse_date_strict(txn_date):
            row_errors.append({
                "rule_id": "TXN_004",
                "entity_type": "Transaction",
                "record_id": txn_id_str,
                "severity": "ERROR",
                "error_message": f"Invalid transaction date: '{txn_date}'.",
                "source_data": source_snapshot
            })

        fatal_errors = [e for e in row_errors if e["severity"] == "ERROR"]
        if fatal_errors:
            exceptions.extend(row_errors)
        else:
            valid_rows.append(row)

    valid_df = pd.DataFrame(valid_rows) if valid_rows else pd.DataFrame(columns=df.columns)
    return valid_df, exceptions

def validate_all_entities(data_dict: dict[str, pd.DataFrame]) -> tuple[dict[str, pd.DataFrame], list[dict]]:
    """
    Executes validation engine across all entities in relational dependency order.
    Returns (valid_data_dict, all_exceptions).
    """
    all_exceptions = []
    valid_data = {}

    # Addresses (Pass-through)
    valid_data["Addresses"] = data_dict.get("Addresses_Legacy", pd.DataFrame())

    # 1. Customers
    cust_df = data_dict.get("Customers_Legacy", pd.DataFrame())
    valid_cust_df, cust_ex = validate_customers(cust_df)
    valid_data["Customers"] = valid_cust_df
    all_exceptions.extend(cust_ex)
    valid_customer_ids = set(valid_cust_df["customer_id"].dropna().astype(str).str.strip().unique())

    # 2. Accounts
    acct_df = data_dict.get("Accounts_Legacy", pd.DataFrame())
    valid_acct_df, acct_ex = validate_accounts(acct_df, valid_customer_ids)
    valid_data["Accounts"] = valid_acct_df
    all_exceptions.extend(acct_ex)
    valid_account_ids = set(valid_acct_df["account_id"].dropna().astype(str).str.strip().unique())

    # 3. Transactions
    txn_df = data_dict.get("Transactions_Legacy", pd.DataFrame())
    valid_txn_df, txn_ex = validate_transactions(txn_df, valid_account_ids)
    valid_data["Transactions"] = valid_txn_df
    all_exceptions.extend(txn_ex)

    # 4. Loans & Beneficiaries
    valid_data["Loans"] = data_dict.get("Loans_Legacy", pd.DataFrame())
    valid_data["Beneficiaries"] = data_dict.get("Beneficiaries_Legacy", pd.DataFrame())

    return valid_data, all_exceptions
