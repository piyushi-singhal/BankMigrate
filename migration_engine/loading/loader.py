import pandas as pd
from migration_engine.config.settings import get_target_engine, get_target_connection

LOAD_ORDER = [
    "Addresses",
    "Customers",
    "Accounts",
    "Transactions",
    "Loans",
    "Beneficiaries"
]

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

def load_entity(df: pd.DataFrame, target_table_name: str) -> int:
    """
    Bulk loads a transformed DataFrame into a target database table using SQLAlchemy engine.
    Returns count of loaded records.
    """
    if df is None or df.empty:
        return 0

    engine = get_target_engine()
    df.to_sql(name=target_table_name, con=engine, if_exists="append", index=False)
    return len(df)

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
