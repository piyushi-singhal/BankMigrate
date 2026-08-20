"""
Milestone 6 Execution Script: Extraction + Profiling
"""
import json
import pandas as pd
from migration_engine.extraction.extractor import extract_legacy_data
from migration_engine.profiling.profiler import profile_all_tables

def run_milestone_6():
    print("=================================================================")
    print("        MILESTONE 6: DATA EXTRACTION & PROFILING RUN           ")
    print("=================================================================\n")

    # 1. Extraction
    print("1. Extracting data from BankMigrate_Legacy database...")
    extracted_data = extract_legacy_data()
    print(f"   Successfully extracted {len(extracted_data)} tables.\n")

    # 2. Profiling
    print("2. Generating profiling statistics for extracted DataFrames...")
    profiles = profile_all_tables(extracted_data)

    for table_name, profile in profiles.items():
        print(f"\n--- Profiling Summary: {table_name} ---")
        print(f"  • Total Row Count: {profile['total_rows']}")
        print(f"  • Duplicate Rows:  {profile['duplicate_rows']}")
        print("  • Null Value Counts per Column:")
        for col, null_cnt in profile['null_counts'].items():
            status = "⚠️ HAS NULLS" if null_cnt > 0 else "OK"
            print(f"      - {col}: {null_cnt} nulls ({status})")

    print("\n=================================================================")
    print("   MILESTONE 6 COMPLETED: EXTRACTION & PROFILING SUCCESSFUL     ")
    print("=================================================================")
    return extracted_data, profiles

if __name__ == "__main__":
    run_milestone_6()
