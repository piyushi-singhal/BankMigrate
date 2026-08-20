"""
Milestone 9 Execution Script: Target Database Loading
"""
import pymssql
import pandas as pd
from migration_engine.extraction.extractor import extract_legacy_data
from migration_engine.validation.validator import validate_all_entities
from migration_engine.transformation.transformer import transform_all_entities
from migration_engine.loading.loader import load_transformed_data
from migration_engine.config.settings import get_target_connection

def run_milestone_9():
    print("=================================================================")
    print("        MILESTONE 9: TARGET DATABASE BULK LOADING              ")
    print("=================================================================\n")

    # 1. Extract
    print("1. Extracting data from BankMigrate_Legacy...")
    extracted_data = extract_legacy_data()

    # 2. Validate
    print("2. Validating records against rule catalog...")
    valid_data, exceptions = validate_all_entities(extracted_data)

    # 3. Transform
    print("3. Transforming valid records to target specifications...")
    transformed_data = transform_all_entities(valid_data)

    # 4. Load
    print("4. Bulk loading clean records into BankMigrate_Target (clearing target tables first)...")
    load_counts = load_transformed_data(transformed_data, clear_first=True)

    print("\n--- LOADED RECORD COUNTS PER TABLE ---")
    for table, count in load_counts.items():
        print(f"  • Table '{table}': {count} records inserted.")

    # 5. SQL Verification
    print("\n5. Verifying target database state directly via T-SQL queries...")
    conn = get_target_connection()
    cursor = conn.cursor()

    total_target_records = 0
    for table in load_counts.keys():
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        db_count = cursor.fetchone()[0]
        total_target_records += db_count
        status = "✅ MATCH" if db_count == load_counts[table] else "❌ MISMATCH"
        print(f"  • DB Verification '{table}': {db_count} rows in SQL Server ({status})")

    conn.close()

    print("\n=================================================================")
    print(f"   MILESTONE 9 COMPLETED: {total_target_records} TOTAL ROWS LOADED SUCCESSFULLY ")
    print("=================================================================")
    return load_counts

if __name__ == "__main__":
    run_milestone_9()
