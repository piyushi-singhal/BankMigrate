import pandas as pd
from migration_engine.config.settings import get_target_engine

def load_entity(df: pd.DataFrame, target_table_name: str) -> int:
    """
    Loads a transformed DataFrame into a target database table using SQLAlchemy engine.
    Returns count of loaded records.
    """
    if df.empty:
        return 0

    engine = get_target_engine()
    df.to_sql(name=target_table_name, con=engine, if_exists="append", index=False)
    return len(df)

def load_transformed_data(transformed_dict: dict[str, pd.DataFrame]) -> dict[str, int]:
    """
    Bulk loads all transformed DataFrames into BankMigrate_Target in proper foreign key dependency order:
    1. Addresses
    2. Customers
    3. Accounts
    4. Transactions
    5. Loans
    6. Beneficiaries
    """
    load_order = ["Addresses", "Customers", "Accounts", "Transactions", "Loans", "Beneficiaries"]
    loaded_counts = {}

    for table in load_order:
        if table in transformed_dict and not transformed_dict[table].empty:
            count = load_entity(transformed_dict[table], table)
            loaded_counts[table] = count
        else:
            loaded_counts[table] = 0

    return loaded_counts
