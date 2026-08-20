import datetime
from migration_engine.audit.logger import create_migration_run, update_migration_run
from migration_engine.extraction.extractor import extract_legacy_data
from migration_engine.profiling.profiler import profile_all_tables
from migration_engine.validation.validator import validate_all_entities
from migration_engine.transformation.transformer import transform_all_entities
from migration_engine.exceptions.handler import record_exceptions
from migration_engine.loading.loader import load_transformed_data
from migration_engine.reconciliation.reconciler import reconcile_run

def run_pipeline(run_id: str = None) -> dict:
    """
    Executes the full end-to-end BankMigrate migration pipeline:
    extract -> profile -> validate -> transform -> load -> reconcile -> report
    """
    if not run_id:
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        run_id = f"RUN-{timestamp_str}"

    print(f"=========================================================")
    print(f"      STARTING MIGRATION RUN: {run_id}")
    print(f"=========================================================\n")

    # Step 0: Initialize Migration Run Tracking
    create_migration_run(run_id)

    # Step 1: Extract Legacy Data
    print("Stage 1: Extracting legacy data...")
    raw_data = extract_legacy_data()
    source_count = sum(len(df) for df in raw_data.values())
    print(f"Extracted {source_count} total records across 6 legacy tables.")

    # Step 2: Data Profiling
    print("\nStage 2: Profiling legacy data...")
    profiles = profile_all_tables(raw_data)
    for table, profile in profiles.items():
        print(f"  - {table}: {profile['total_rows']} rows, {profile['duplicate_rows']} duplicates.")

    # Step 3: Data Validation
    print("\nStage 3: Validating records against rule catalog...")
    valid_data, exceptions = validate_all_entities(raw_data)
    validated_count = sum(len(df) for df in valid_data.values())
    rejected_count = len(exceptions)
    print(f"Validation finished: {validated_count} valid records, {rejected_count} exceptions isolated.")

    # Step 4: Exception Handling
    print("\nStage 4: Isolating rejected records into exception store...")
    recorded_exceptions_count = record_exceptions(run_id, exceptions)
    print(f"Recorded {recorded_exceptions_count} exception records into MigrationExceptions.")

    # Step 5: Transformation
    print("\nStage 5: Transforming valid records to target schema...")
    transformed_data = transform_all_entities(valid_data)
    transformed_count = sum(len(df) for df in transformed_data.values())
    print(f"Transformed {transformed_count} records to target specifications.")

    # Step 6: Target Loading
    print("\nStage 6: Bulk loading transformed records to target database...")
    load_counts = load_transformed_data(transformed_data)
    loaded_count = sum(load_counts.values())
    print(f"Successfully loaded {loaded_count} records into BankMigrate_Target.")

    # Step 7: Reconciliation
    print("\nStage 7: Executing reconciliation...")
    summary_counts = {
        "source_records": source_count,
        "validated_records": validated_count,
        "transformed_records": transformed_count,
        "loaded_records": loaded_count,
        "rejected_records": rejected_count
    }
    reconciliation_report = reconcile_run(run_id, summary_counts)
    print(f"Reconciliation Status: {reconciliation_report['status']}")

    # Step 8: Update Migration Run State & Report
    final_status = "COMPLETED_WITH_EXCEPTIONS" if rejected_count > 0 else "COMPLETED"
    update_migration_run(run_id, summary_counts, final_status)

    print(f"\n=========================================================")
    print(f"      MIGRATION RUN {run_id} FINISHED: {final_status}")
    print(f"=========================================================\n")

    return {
        "run_id": run_id,
        "status": final_status,
        "summary_counts": summary_counts,
        "reconciliation": reconciliation_report
    }

if __name__ == "__main__":
    run_pipeline()
