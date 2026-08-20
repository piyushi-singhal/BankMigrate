import pandas as pd
from migration_engine.config.settings import get_legacy_engine

LEGACY_TABLES = [
    "Addresses_Legacy",
    "Customers_Legacy",
    "Accounts_Legacy",
    "Transactions_Legacy",
    "Loans_Legacy",
    "Beneficiaries_Legacy"
]

def extract_table(table_name: str) -> pd.DataFrame:
    """
    Extracts all rows from a single legacy database table into a pandas DataFrame.
    """
    engine = get_legacy_engine()
    query = f"SELECT * FROM {table_name};"
    df = pd.read_sql(query, con=engine)
    return df

def extract_legacy_data() -> dict[str, pd.DataFrame]:
    """
    Extracts all 6 legacy banking tables into a dictionary of DataFrames.
    """
    data = {}
    for table in LEGACY_TABLES:
        data[table] = extract_table(table)
    return data
