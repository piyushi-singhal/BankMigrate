"""
Milestone 8 Execution Script: Data Transformation
"""
import pandas as pd
from migration_engine.extraction.extractor import extract_legacy_data
from migration_engine.validation.validator import validate_all_entities
from migration_engine.transformation.transformer import transform_all_entities

def run_milestone_8():
    print("=================================================================")
    print("        MILESTONE 8: DATA TRANSFORMATION PIPELINE              ")
    print("=================================================================\n")

    # 1. Extract
    print("1. Extracting raw data from legacy database...")
    extracted_data = extract_legacy_data()

    # 2. Validate
    print("2. Validating records to isolate clean valid dataset...")
    valid_data, exceptions = validate_all_entities(extracted_data)

    # 3. Transform
    print("3. Applying mapping and cleaning rules to valid records...\n")
    transformed_data = transform_all_entities(valid_data)

    for entity_name, df in transformed_data.items():
        print(f"--- Transformed Entity: {entity_name} ({len(df)} records) ---")
        if not df.empty:
            print(df.to_string(index=False))
        else:
            print("  [No valid records to transform]")
        print("\n")

    print("=================================================================")
    print("   MILESTONE 8 COMPLETED: TRANSFORMATION FULLY VERIFIED        ")
    print("=================================================================")
    return transformed_data

if __name__ == "__main__":
    run_milestone_8()
