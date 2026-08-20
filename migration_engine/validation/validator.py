import re
import pandas as pd
from datetime import datetime
from .rules import VALIDATION_RULES

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

def validate_customers(df: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    """
    Validates Customers_Legacy DataFrame. Returns (valid_df, exceptions_list).
    """
    valid_rows = []
    exceptions = []
    seen_natural_keys = set()

    for _, row in df.iterrows():
        cust_id = row.get("customer_id")
        cust_name = str(row.get("customer_name") or "").strip()
        dob = str(row.get("dob") or "").strip()
        email = str(row.get("email") or "").strip()

        row_errors = []

        # CUSTOMER_001: Missing Customer ID
        if pd.isna(cust_id) or not str(cust_id).strip():
            row_errors.append({
                "rule_id": "CUSTOMER_001",
                "entity_type": "Customer",
                "record_id": str(cust_id),
                "severity": "ERROR",
                "error_message": "Customer ID is NULL or empty.",
                "source_data": row.to_json()
            })

        # CUSTOMER_002: Duplicate Customer
        natural_key = (cust_name.lower(), dob)
        if natural_key in seen_natural_keys and cust_id is not None:
            row_errors.append({
                "rule_id": "CUSTOMER_002",
                "entity_type": "Customer",
                "record_id": str(cust_id),
                "severity": "ERROR",
                "error_message": f"Duplicate customer detected for name '{cust_name}' and DOB '{dob}'.",
                "source_data": row.to_json()
            })
        else:
            if cust_id is not None:
                seen_natural_keys.add(natural_key)

        # CUSTOMER_004: Invalid Email
        if email and not EMAIL_REGEX.match(email):
            row_errors.append({
                "rule_id": "CUSTOMER_004",
                "entity_type": "Customer",
                "record_id": str(cust_id),
                "severity": "ERROR",
                "error_message": f"Invalid email format: '{email}'.",
                "source_data": row.to_json()
            })

        # CUSTOMER_005: Invalid DOB
        if dob:
            try:
                if "/" in dob:
                    datetime.strptime(dob, "%d/%m/%Y")
                else:
                    datetime.strptime(dob, "%Y-%m-%d")
            except ValueError:
                row_errors.append({
                    "rule_id": "CUSTOMER_005",
                    "entity_type": "Customer",
                    "record_id": str(cust_id),
                    "severity": "ERROR",
                    "error_message": f"Invalid date of birth: '{dob}'.",
                    "source_data": row.to_json()
                })

        if row_errors:
            exceptions.extend(row_errors)
        else:
            valid_rows.append(row)

    valid_df = pd.DataFrame(valid_rows) if valid_rows else pd.DataFrame(columns=df.columns)
    return valid_df, exceptions

def validate_accounts(df: pd.DataFrame, valid_customer_ids: set) -> tuple[pd.DataFrame, list[dict]]:
    """
    Validates Accounts_Legacy DataFrame.
    """
    valid_rows = []
    exceptions = []

    for _, row in df.iterrows():
        acct_id = row.get("account_id")
        cust_id = row.get("customer_id")
        acct_type = str(row.get("account_type") or "").strip().upper()
        balance = row.get("balance")

        row_errors = []

        # ACCOUNT_001: Missing Account ID
        if pd.isna(acct_id) or not str(acct_id).strip():
            row_errors.append({
                "rule_id": "ACCOUNT_001",
                "entity_type": "Account",
                "record_id": str(acct_id),
                "severity": "ERROR",
                "error_message": "Account ID is NULL or empty.",
                "source_data": row.to_json()
            })

        # ACCOUNT_002: Customer FK check
        if cust_id not in valid_customer_ids:
            row_errors.append({
                "rule_id": "ACCOUNT_002",
                "entity_type": "Account",
                "record_id": str(acct_id),
                "severity": "ERROR",
                "error_message": f"Referenced customer '{cust_id}' does not exist in valid Customers.",
                "source_data": row.to_json()
            })

        # ACCOUNT_004: Negative Balance on Savings/Checking
        if acct_type in ("SAVINGS", "CHECKING") and balance is not None and float(balance) < 0:
            row_errors.append({
                "rule_id": "ACCOUNT_004",
                "entity_type": "Account",
                "record_id": str(acct_id),
                "severity": "ERROR",
                "error_message": f"Invalid negative balance ({balance}) on {acct_type} account.",
                "source_data": row.to_json()
            })

        if row_errors:
            exceptions.extend(row_errors)
        else:
            valid_rows.append(row)

    valid_df = pd.DataFrame(valid_rows) if valid_rows else pd.DataFrame(columns=df.columns)
    return valid_df, exceptions

def validate_transactions(df: pd.DataFrame, valid_account_ids: set) -> tuple[pd.DataFrame, list[dict]]:
    """
    Validates Transactions_Legacy DataFrame.
    """
    valid_rows = []
    exceptions = []
    seen_txns = set()

    for _, row in df.iterrows():
        txn_id = row.get("transaction_id")
        acct_id = row.get("account_id")
        amount = row.get("amount")

        row_errors = []

        # TXN_001: Missing Transaction ID
        if pd.isna(txn_id) or not str(txn_id).strip():
            row_errors.append({
                "rule_id": "TXN_001",
                "entity_type": "Transaction",
                "record_id": str(txn_id),
                "severity": "ERROR",
                "error_message": "Transaction ID is NULL or empty.",
                "source_data": row.to_json()
            })

        # TXN_005: Duplicate Transaction
        if txn_id in seen_txns:
            row_errors.append({
                "rule_id": "TXN_005",
                "entity_type": "Transaction",
                "record_id": str(txn_id),
                "severity": "ERROR",
                "error_message": f"Duplicate transaction ID '{txn_id}' detected.",
                "source_data": row.to_json()
            })
        else:
            if txn_id is not None:
                seen_txns.add(txn_id)

        # TXN_002: Account FK check
        if acct_id not in valid_account_ids:
            row_errors.append({
                "rule_id": "TXN_002",
                "entity_type": "Transaction",
                "record_id": str(txn_id),
                "severity": "ERROR",
                "error_message": f"Referenced account '{acct_id}' does not exist in valid Accounts.",
                "source_data": row.to_json()
            })

        # TXN_003: Negative Amount check
        if amount is not None and float(amount) <= 0:
            row_errors.append({
                "rule_id": "TXN_003",
                "entity_type": "Transaction",
                "record_id": str(txn_id),
                "severity": "ERROR",
                "error_message": f"Invalid transaction amount: {amount}.",
                "source_data": row.to_json()
            })

        if row_errors:
            exceptions.extend(row_errors)
        else:
            valid_rows.append(row)

    valid_df = pd.DataFrame(valid_rows) if valid_rows else pd.DataFrame(columns=df.columns)
    return valid_df, exceptions

def validate_all_entities(data_dict: dict[str, pd.DataFrame]) -> tuple[dict[str, pd.DataFrame], list[dict]]:
    """
    Applies validation rules to all extracted DataFrames in proper dependency order.
    Returns (valid_data_dict, all_exceptions_list).
    """
    all_exceptions = []
    valid_data = {}

    # Addresses (Pass-through for now)
    valid_data["Addresses"] = data_dict.get("Addresses_Legacy", pd.DataFrame())

    # 1. Customers
    cust_df = data_dict.get("Customers_Legacy", pd.DataFrame())
    valid_cust_df, cust_ex = validate_customers(cust_df)
    valid_data["Customers"] = valid_cust_df
    all_exceptions.extend(cust_ex)
    valid_customer_ids = set(valid_cust_df["customer_id"].dropna().unique())

    # 2. Accounts
    acct_df = data_dict.get("Accounts_Legacy", pd.DataFrame())
    valid_acct_df, acct_ex = validate_accounts(acct_df, valid_customer_ids)
    valid_data["Accounts"] = valid_acct_df
    all_exceptions.extend(acct_ex)
    valid_account_ids = set(valid_acct_df["account_id"].dropna().unique())

    # 3. Transactions
    txn_df = data_dict.get("Transactions_Legacy", pd.DataFrame())
    valid_txn_df, txn_ex = validate_transactions(txn_df, valid_account_ids)
    valid_data["Transactions"] = valid_txn_df
    all_exceptions.extend(txn_ex)

    # 4. Loans & Beneficiaries (Pass-through for valid accounts/customers)
    valid_data["Loans"] = data_dict.get("Loans_Legacy", pd.DataFrame())
    valid_data["Beneficiaries"] = data_dict.get("Beneficiaries_Legacy", pd.DataFrame())

    return valid_data, all_exceptions
