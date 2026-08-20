import datetime
import pymssql
from migration_engine.config.settings import get_target_connection

def create_migration_run(run_id: str) -> str:
    """
    Creates or resets a MigrationRuns record with status 'IN_PROGRESS'.
    """
    conn = get_target_connection()
    cursor = conn.cursor()

    now = datetime.datetime.now(datetime.timezone.utc)
    query = """
    IF NOT EXISTS (SELECT 1 FROM MigrationRuns WHERE run_id = %s)
    BEGIN
        INSERT INTO MigrationRuns 
        (run_id, started_at, source_records, validated_records, transformed_records, loaded_records, rejected_records, status)
        VALUES (%s, %s, 0, 0, 0, 0, 0, 'IN_PROGRESS');
    END
    ELSE
    BEGIN
        UPDATE MigrationRuns
        SET started_at = %s, completed_at = NULL, status = 'IN_PROGRESS'
        WHERE run_id = %s;
    END
    """
    cursor.execute(query, (run_id, run_id, now, now, run_id))
    conn.close()
    return run_id

def update_migration_run(run_id: str, counts: dict, status: str) -> None:
    """
    Updates a MigrationRuns record with final record counts and run status.
    """
    conn = get_target_connection()
    cursor = conn.cursor()

    now = datetime.datetime.now(datetime.timezone.utc)
    query = """
    UPDATE MigrationRuns
    SET completed_at = %s,
        source_records = %s,
        validated_records = %s,
        transformed_records = %s,
        loaded_records = %s,
        rejected_records = %s,
        status = %s
    WHERE run_id = %s
    """
    cursor.execute(query, (
        now,
        counts.get("source_records", 0),
        counts.get("validated_records", 0),
        counts.get("transformed_records", 0),
        counts.get("loaded_records", 0),
        counts.get("rejected_records", 0),
        status,
        run_id
    ))
    conn.close()

def log_audit_event(run_id: str, entity: str, record_id: str, operation: str, status: str = "SUCCESS") -> None:
    """
    Logs an individual DML operation event into MigrationAudit.
    """
    conn = get_target_connection()
    cursor = conn.cursor()

    now = datetime.datetime.now(datetime.timezone.utc)
    query = """
    INSERT INTO MigrationAudit (run_id, entity, record_id, operation, timestamp, status)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (run_id, entity, str(record_id), operation, now, status))
    conn.close()

def log_audit_batch(run_id: str, entity: str, record_ids: list, operation: str, status: str = "SUCCESS") -> int:
    """
    Logs a batch of DML operations into MigrationAudit.
    """
    if not record_ids:
        return 0

    conn = get_target_connection()
    cursor = conn.cursor()
    now = datetime.datetime.now(datetime.timezone.utc)

    query = """
    INSERT INTO MigrationAudit (run_id, entity, record_id, operation, timestamp, status)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    count = 0
    for rid in record_ids:
        if rid is not None:
            cursor.execute(query, (run_id, entity, str(rid), operation, now, status))
            count += 1
    conn.close()
    return count

def get_run_summary(run_id: str) -> dict:
    """
    Retrieves run state summary for a specific run ID from MigrationRuns.
    """
    conn = get_target_connection()
    cursor = conn.cursor(as_dict=True)
    cursor.execute("SELECT * FROM MigrationRuns WHERE run_id = %s;", (run_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def get_run_audit_logs(run_id: str) -> list[dict]:
    """
    Retrieves all audit entries logged for a specific run ID from MigrationAudit.
    """
    conn = get_target_connection()
    cursor = conn.cursor(as_dict=True)
    cursor.execute("SELECT * FROM MigrationAudit WHERE run_id = %s ORDER BY audit_id ASC;", (run_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows
