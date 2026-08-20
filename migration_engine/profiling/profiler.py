import pandas as pd

def profile_dataframe(df: pd.DataFrame, entity_name: str) -> dict:
    """
    Computes profiling metrics (total rows, null counts, duplicate counts) for a DataFrame.
    """
    total_rows = len(df)
    null_counts = df.isnull().sum().to_dict()
    duplicate_rows = int(df.duplicated().sum())

    return {
        "entity": entity_name,
        "total_rows": total_rows,
        "null_counts": null_counts,
        "duplicate_rows": duplicate_rows
    }

def profile_all_tables(data_dict: dict[str, pd.DataFrame]) -> dict:
    """
    Profiles all extracted legacy DataFrames.
    """
    profiles = {}
    for table_name, df in data_dict.items():
        profiles[table_name] = profile_dataframe(df, table_name)
    return profiles
