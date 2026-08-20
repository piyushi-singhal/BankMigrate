from migration_engine.config.settings import get_target_connection

def reconcile_run(run_id: str, summary_counts: dict) -> dict:
    """
    Computes mathematical reconciliation for a run ID:
    Checks if Source Records = Valid Records + Rejected Records = Loaded Records + Rejected Records.
    """
    source = summary_counts.get("source_records", 0)
    valid = summary_counts.get("validated_records", 0)
    rejected = summary_counts.get("rejected_records", 0)
    loaded = summary_counts.get("loaded_records", 0)

    count_match = (source == (valid + rejected)) and (valid == loaded)

    reconciliation_report = {
        "run_id": run_id,
        "source_records": source,
        "validated_records": valid,
        "rejected_records": rejected,
        "loaded_records": loaded,
        "count_match": count_match,
        "status": "BALANCED" if count_match else "DISCREPANCY_DETECTED"
    }

    return reconciliation_report
