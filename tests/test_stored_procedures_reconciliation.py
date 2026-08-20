import pytest
from migration_engine.reconciliation.reconciler import reconcile_run
from migration_engine.config.settings import get_target_connection

def test_stored_procedures_deployment_and_execution():
    conn = get_target_connection()
    cursor = conn.cursor(as_dict=True)
    
    # Test sp_detect_duplicates
    cursor.callproc("sp_detect_duplicates")
    assert cursor is not None
    
    # Test sp_reconcile_migration
    cursor.callproc("sp_reconcile_migration", ("RUN-TEST-M10-M12",))
    rows = cursor.fetchall()
    assert len(rows) > 0
    assert "reconciliation_status" in rows[0]
    conn.close()

def test_reconciliation_math():
    summary_counts = {
        "source_records": 38,
        "validated_records": 29,
        "transformed_records": 29,
        "loaded_records": 29,
        "rejected_records": 9
    }
    report = reconcile_run("RUN-TEST-RECON-PYTEST", summary_counts)
    assert report["count_match"] is True
    assert report["status"] == "BALANCED"
