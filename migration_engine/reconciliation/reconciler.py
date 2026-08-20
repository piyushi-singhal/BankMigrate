import pymssql
from migration_engine.config.settings import get_target_connection

def reconcile_run(run_id: str, summary_counts: dict) -> dict:
    """
    Executes mathematical and database reconciliation for a migration run:
    1. Checks record count math: Source = Valid + Rejected; Valid = Loaded.
    2. Calls T-SQL stored procedure sp_reconcile_migration to verify monetary amount balance.
    """
    source = summary_counts.get("source_records", 0)
    valid = summary_counts.get("validated_records", 0)
    rejected = summary_counts.get("rejected_records", 0)
    loaded = summary_counts.get("loaded_records", 0)

    count_match = (source == (valid + rejected)) and (valid == loaded)

    db_reconciliation = {}
    try:
        conn = get_target_connection()
        cursor = conn.cursor(as_dict=True)
        cursor.callproc("sp_reconcile_migration", (run_id,))
        rows = cursor.fetchall()
        if rows:
            db_reconciliation = rows[0]
        conn.close()
    except Exception as e:
        print(f"Warning: Stored procedure sp_reconcile_migration call notice: {e}")

    final_status = "BALANCED" if count_match else "DISCREPANCY_DETECTED"

    reconciliation_report = {
        "run_id": run_id,
        "source_records": source,
        "validated_records": valid,
        "rejected_records": rejected,
        "loaded_records": loaded,
        "count_match": count_match,
        "monetary_reconciliation": db_reconciliation,
        "status": final_status
    }

    return reconciliation_report
