import pytest
from migration_engine.pipeline import run_pipeline
from migration_engine.audit.logger import get_run_summary, get_run_audit_logs

def test_full_end_to_end_pipeline():
    run_id = "RUN-E2E-PYTEST"
    result = run_pipeline(run_id=run_id, clear_target=True)
    
    assert result["status"] == "COMPLETED_WITH_EXCEPTIONS"
    assert result["summary_counts"]["source_records"] == 38
    assert result["summary_counts"]["validated_records"] == 29
    assert result["summary_counts"]["rejected_records"] == 9
    assert result["summary_counts"]["loaded_records"] == 29
    assert result["reconciliation"]["count_match"] is True

    # Verify SQL Server Run Summary
    run_summary = get_run_summary(run_id)
    assert run_summary is not None
    assert run_summary["status"] == "COMPLETED_WITH_EXCEPTIONS"
    
    # Verify Audit Logs in SQL Server
    audit_logs = get_run_audit_logs(run_id)
    assert len(audit_logs) > 0

def test_pipeline_failure_injection_and_recovery():
    # Test Failure Injection
    fail_res = run_pipeline(run_id="RUN-FAIL-E2E", failure_mode="NETWORK_DROP")
    assert fail_res["status"] == "FAILED"
    
    # Test Recovery
    rec_res = run_pipeline(run_id="RUN-FAIL-E2E", clear_target=True, failure_mode=None)
    assert rec_res["status"] == "COMPLETED_WITH_EXCEPTIONS"
    assert rec_res["summary_counts"]["loaded_records"] == 29
