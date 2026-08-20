import pandas as pd
import pymssql
from migration_engine.config.settings import get_target_engine, get_target_connection

LOAD_ORDER = [
    "Addresses",
    "Customers",
    "Accounts",
    "Transactions",
    "Loans",
    "Beneficiaries"
]

PK_MAP = {
    "Addresses": "address_id",
    "Customers": "customer_id",
    "Accounts": "account_id",
    "Transactions": "transaction_id",
    "Loans": "loan_id",
    "Beneficiaries": "beneficiary_id"
}

def clear_target_tables() -> None:
    """
    Truncates/clears target banking tables in reverse foreign key order before loading.
    """
    conn = get_target_connection()
    cursor = conn.cursor()
    
    # Delete in reverse foreign key dependency order
    reverse_order = list(reversed(LOAD_ORDER))
    for table in reverse_order:
        cursor.execute(f"DELETE FROM {table};")
    
    conn.close()

def get_existing_pks(target_table_name: str, pk_col: str) -> set:
    """
    Queries existing Primary Keys in target database table.
    """
    try:
        conn = get_target_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT {pk_col} FROM {target_table_name};")
        rows = cursor.fetchall()
        conn.close()
        return set(str(r[0]) for r in rows if r[0] is not None)
    except Exception:
        return set()

def load_entity(df: pd.DataFrame, target_table_name: str) -> int:
    """
    Bulk loads a transformed DataFrame into a target database table using SQLAlchemy engine.
    Filters out primary keys already present in target table to avoid duplicate key violations.
    Returns count of newly loaded records.
    """
    if df is None or df.empty:
        return 0

    pk_col = PK_MAP.get(target_table_name)
    load_df = df.copy()

    if pk_col and pk_col in load_df.columns:
        existing_pks = get_existing_pks(target_table_name, pk_col)
        if existing_pks:
            load_df = load_df[~load_df[pk_col].astype(str).str.strip().isin(existing_pks)]

    if load_df.empty:
        return 0

    engine = get_target_engine()
    load_df.to_sql(name=target_table_name, con=engine, if_exists="append", index=False)
    return len(load_df)

def load_transformed_data(transformed_dict: dict[str, pd.DataFrame], clear_first: bool = False) -> dict[str, int]:
    """
    Bulk loads all transformed DataFrames into BankMigrate_Target in proper foreign key dependency order.
    """
    if clear_first:
        clear_target_tables()

    loaded_counts = {}

    for table in LOAD_ORDER:
        if table in transformed_dict and not transformed_dict[table].empty:
            count = load_entity(transformed_dict[table], table)
            loaded_counts[table] = count
        else:
            loaded_counts[table] = 0

    return loaded_counts
