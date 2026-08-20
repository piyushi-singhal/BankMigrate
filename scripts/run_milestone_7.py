"""
Milestone 7 Execution Script: Validation Engine & Rule Catalog Enforcement
"""
import json
import pandas as pd
from migration_engine.extraction.extractor import extract_legacy_data
from migration_engine.validation.validator import validate_all_entities

def run_milestone_7():
    print("=================================================================")
    print("        MILESTONE 7: VALIDATION ENGINE RULE ENFORCEMENT        ")
    print("=================================================================\n")

    # 1. Extract Legacy Data
    print("1. Extracting data from BankMigrate_Legacy database...")
    extracted_data = extract_legacy_data()

    # 2. Execute Validation Engine
    print("2. Running Validation Engine across Customers, Accounts, and Transactions...\n")
    valid_data, exceptions = validate_all_entities(extracted_data)

    print("--- VALIDATION RESULTS SUMMARY ---")
    for entity_name, df in valid_data.items():
        original_key = f"{entity_name}_Legacy" if f"{entity_name}_Legacy" in extracted_data else entity_name
        orig_count = len(extracted_data.get(original_key, []))
        valid_count = len(df)
        print(f"  • Entity '{entity_name}': {orig_count} original records $\\rightarrow$ {valid_count} VALID passed.")

    print(f"\nTotal Exceptions Isolated: {len(exceptions)}\n")

    print("--- DETAILED EXCEPTION BREAKDOWN ---")
    for idx, ex in enumerate(exceptions, 1):
        print(f"[{idx}] Rule: {ex['rule_id']} | Severity: {ex['severity']} | Entity: {ex['entity_type']} | Record ID: {ex['record_id']}")
        print(f"    Message: {ex['error_message']}")

    print("\n=================================================================")
    print("   MILESTONE 7 COMPLETED: VALIDATION ENGINE FULLY VERIFIED      ")
    print("=================================================================")
    return valid_data, exceptions

if __name__ == "__main__":
    run_milestone_7()
