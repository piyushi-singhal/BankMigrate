import pymssql
from migration_engine.config.settings import get_target_connection

def record_exceptions(run_id: str, exceptions_list: list[dict]) -> int:
    """
    Inserts a list of rejected record exceptions into the MigrationExceptions table.
    """
    if not exceptions_list:
        return 0

    conn = get_target_connection()
    cursor = conn.cursor()

    query = """
    INSERT INTO MigrationExceptions 
    (run_id, entity_type, record_id, rule_id, severity, error_message, source_data, status)
    VALUES (%s, %s, %s, %s, %s, %s, %s, 'OPEN')
    """

    inserted = 0
    for ex in exceptions_list:
        cursor.execute(query, (
            run_id,
            ex.get("entity_type", "Unknown"),
            str(ex.get("record_id")) if ex.get("record_id") is not None else None,
            ex.get("rule_id", "GENERAL_ERROR"),
            ex.get("severity", "ERROR"),
            ex.get("error_message", ""),
            str(ex.get("source_data", ""))
        ))
        inserted += 1

    conn.close()
    return inserted

def get_run_exceptions(run_id: str) -> list[dict]:
    """
    Retrieves all exception records logged for a specific run ID.
    """
    conn = get_target_connection()
    cursor = conn.cursor(as_dict=True)

    cursor.execute("SELECT * FROM MigrationExceptions WHERE run_id = %s;", (run_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows
