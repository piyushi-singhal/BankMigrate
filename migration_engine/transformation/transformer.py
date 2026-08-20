import re
import pandas as pd
from datetime import datetime

def normalize_phone(phone_str: str) -> str:
    if not phone_str or pd.isna(phone_str):
        return ""
    digits = re.sub(r"\D", "", str(phone_str))
    if len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    return digits

def parse_iso_date(date_str: str) -> str:
    if not date_str or pd.isna(date_str):
        return None
    s = str(date_str).strip()
    try:
        if "/" in s:
            dt = datetime.strptime(s, "%d/%m/%Y")
        else:
            dt = datetime.strptime(s[:10], "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return s

def transform_customers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms valid Customers DataFrame to match target Customers schema.
    """
    if df.empty:
        return pd.DataFrame(columns=["customer_id", "full_name", "date_of_birth", "phone_number", "email", "address_id"])

    tf_df = pd.DataFrame()
    tf_df["customer_id"] = df["customer_id"].astype(str).str.strip()
    tf_df["full_name"] = df["customer_name"].astype(str).str.strip().str.title()
    tf_df["date_of_birth"] = df["dob"].apply(parse_iso_date)
    tf_df["phone_number"] = df["phone"].apply(normalize_phone)
    tf_df["email"] = df["email"].astype(str).str.strip().str.lower()
    tf_df["address_id"] = df["address_id"].astype(str).str.strip()
    return tf_df

def transform_accounts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms valid Accounts DataFrame to match target Accounts schema.
    """
    if df.empty:
        return pd.DataFrame(columns=["account_id", "customer_id", "account_type", "balance", "opened_date", "status"])

    tf_df = pd.DataFrame()
    tf_df["account_id"] = df["account_id"].astype(str).str.strip()
    tf_df["customer_id"] = df["customer_id"].astype(str).str.strip()
    tf_df["account_type"] = df["account_type"].astype(str).str.strip().str.upper()
    tf_df["balance"] = df["balance"].astype(float).round(2)
    tf_df["opened_date"] = df["opened_date"].apply(parse_iso_date)
    tf_df["status"] = df["status"].astype(str).str.strip().str.upper()
    return tf_df

def transform_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms valid Transactions DataFrame to match target Transactions schema.
    """
    if df.empty:
        return pd.DataFrame(columns=["transaction_id", "account_id", "transaction_type", "amount", "transaction_date", "description"])

    tf_df = pd.DataFrame()
    tf_df["transaction_id"] = df["transaction_id"].astype(str).str.strip()
    tf_df["account_id"] = df["account_id"].astype(str).str.strip()
    tf_df["transaction_type"] = df["transaction_type"].astype(str).str.strip().str.upper()
    tf_df["amount"] = df["amount"].astype(float).round(2)
    tf_df["transaction_date"] = df["transaction_date"].astype(str).str.strip()
    tf_df["description"] = df["description"].astype(str).str.strip()
    return tf_df

def transform_all_entities(valid_data_dict: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """
    Transforms all valid entity DataFrames to target schemas.
    """
    transformed = {}
    
    if "Addresses" in valid_data_dict:
        addr_df = valid_data_dict["Addresses"].copy()
        if not addr_df.empty:
            addr_df["address_id"] = addr_df["address_id"].astype(str).str.strip()
            addr_df["street_address"] = addr_df["street_address"].astype(str).str.strip()
            addr_df["city"] = addr_df["city"].astype(str).str.strip().str.title()
            addr_df["state"] = addr_df["state"].astype(str).str.strip().str.upper()
            addr_df["postal_code"] = addr_df["postal_code"].astype(str).str.strip()
            addr_df["country"] = addr_df["country"].astype(str).str.strip().str.upper()
        transformed["Addresses"] = addr_df

    if "Customers" in valid_data_dict:
        transformed["Customers"] = transform_customers(valid_data_dict["Customers"])

    if "Accounts" in valid_data_dict:
        transformed["Accounts"] = transform_accounts(valid_data_dict["Accounts"])

    if "Transactions" in valid_data_dict:
        transformed["Transactions"] = transform_transactions(valid_data_dict["Transactions"])

    if "Loans" in valid_data_dict:
        loans_df = valid_data_dict["Loans"].copy()
        if not loans_df.empty:
            loans_df["loan_id"] = loans_df["loan_id"].astype(str).str.strip()
            loans_df["account_id"] = loans_df["account_id"].astype(str).str.strip()
            loans_df["loan_amount"] = loans_df["loan_amount"].astype(float).round(2)
            loans_df["interest_rate"] = loans_df["interest_rate"].astype(float).round(2)
            loans_df["term_months"] = loans_df["term_months"].astype(int)
            loans_df["start_date"] = loans_df["start_date"].apply(parse_iso_date)
        transformed["Loans"] = loans_df

    if "Beneficiaries" in valid_data_dict:
        ben_df = valid_data_dict["Beneficiaries"].copy()
        if not ben_df.empty:
            ben_df["beneficiary_id"] = ben_df["beneficiary_id"].astype(str).str.strip()
            ben_df["customer_id"] = ben_df["customer_id"].astype(str).str.strip()
            ben_df["beneficiary_name"] = ben_df["beneficiary_name"].astype(str).str.strip().str.title()
            ben_df["account_number"] = ben_df["account_number"].astype(str).str.strip()
            ben_df["routing_code"] = ben_df["routing_code"].astype(str).str.strip().str.upper()
        transformed["Beneficiaries"] = ben_df

    return transformed
