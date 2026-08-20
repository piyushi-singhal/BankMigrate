import datetime
from migration_engine.audit.logger import (
    create_migration_run,
    update_migration_run,
    log_audit_event,
    log_audit_batch
)
from migration_engine.extraction.extractor import extract_legacy_data
from migration_engine.profiling.profiler import profile_all_tables
from migration_engine.validation.validator import validate_all_entities
from migration_engine.transformation.transformer import transform_all_entities
from migration_engine.exceptions.handler import record_exceptions
from migration_engine.exceptions.simulator import inject_failure_if_requested, MigrationFailureException
from migration_engine.loading.loader import load_transformed_data
from migration_engine.reconciliation.reconciler import reconcile_run

def run_pipeline(run_id: str = None, clear_target: bool = True, failure_mode: str = None) -> dict:
    """
    Executes the full end-to-end BankMigrate migration pipeline:
    extract -> profile -> validate -> transform -> load -> reconcile -> report -> audit
    Includes failure injection hooks and exception-safe status updates.
    """
    if not run_id:
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        run_id = f"RUN-{timestamp_str}"

    print(f"=========================================================")
    print(f"      STARTING MIGRATION RUN: {run_id}")
    if failure_mode:
        print(f"      [FAILURE MODE INJECTED: {failure_mode}]")
    print(f"=========================================================\n")

    # Step 0: Initialize Migration Run Tracking
    create_migration_run(run_id)

    try:
        # Step 1: Extract Legacy Data
        print("Stage 1: Extracting legacy data...")
        inject_failure_if_requested(failure_mode, "extraction")
        raw_data = extract_legacy_data()
        source_count = sum(len(df) for df in raw_data.values())
        print(f"Extracted {source_count} total records across 6 legacy tables.")

        # Step 2: Data Profiling
        print("\nStage 2: Profiling legacy data...")
        profiles = profile_all_tables(raw_data)

        # Step 3: Data Validation
        print("\nStage 3: Validating records against rule catalog...")
        inject_failure_if_requested(failure_mode, "validation")
        valid_data, exceptions = validate_all_entities(raw_data)
        validated_count = sum(len(df) for df in valid_data.values())
        rejected_count = len(exceptions)
        print(f"Validation finished: {validated_count} valid records, {rejected_count} exceptions isolated.")

        # Step 4: Exception Handling & Audit Rejections
        print("\nStage 4: Isolating rejected records into exception store...")
        recorded_exceptions_count = record_exceptions(run_id, exceptions)
        
        # Audit log rejected records
        rejected_ids = [ex.get("record_id") for ex in exceptions if ex.get("record_id") is not None]
        log_audit_batch(run_id, "MultiEntity", rejected_ids, "REJECT", "SUCCESS")

        # Step 5: Transformation
        print("\nStage 5: Transforming valid records to target schema...")
        transformed_data = transform_all_entities(valid_data)
        transformed_count = sum(len(df) for df in transformed_data.values())

        # Step 6: Target Loading & Audit Inserts
        print("\nStage 6: Bulk loading transformed records to target database...")
        inject_failure_if_requested(failure_mode, "loading")
        load_counts = load_transformed_data(transformed_data, clear_first=clear_target)
        loaded_count = sum(load_counts.values())
        print(f"Successfully loaded {loaded_count} records into BankMigrate_Target.")

        # Audit log inserted records per entity
        for entity_name, df in transformed_data.items():
            if not df.empty:
                pk_col = "address_id" if entity_name == "Addresses" else \
                         "customer_id" if entity_name == "Customers" else \
                         "account_id" if entity_name == "Accounts" else \
                         "transaction_id" if entity_name == "Transactions" else \
                         "loan_id" if entity_name == "Loans" else "beneficiary_id"

                if pk_col in df.columns:
                    rec_ids = df[pk_col].dropna().tolist()
                    log_audit_batch(run_id, entity_name, rec_ids, "INSERT", "SUCCESS")

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

    except Exception as e:
        print(f"\n[PIPELINE EXCEPTION CAPTURED] Run '{run_id}' encountered error: {e}")
        failure_counts = {
            "source_records": 0,
            "validated_records": 0,
            "transformed_records": 0,
            "loaded_records": 0,
            "rejected_records": 0
        }
        update_migration_run(run_id, failure_counts, "FAILED")
        log_audit_event(run_id, "Pipeline", run_id, "PIPELINE_FAILURE", status="FAILURE")
        
        return {
            "run_id": run_id,
            "status": "FAILED",
            "error": str(e)
        }

if __name__ == "__main__":
    run_pipeline()
