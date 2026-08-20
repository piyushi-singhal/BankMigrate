import os
import pymssql
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "1433"))
DB_USER = os.getenv("DB_USER", "sa")
DB_PASSWORD = os.getenv("DB_PASSWORD", "BankMigrate123!")
DB_NAME = os.getenv("DB_TARGET_NAME", "BankMigrate_Target")

def deploy_stored_procedures():
    print(f"Connecting to SQL Server database '{DB_NAME}'...")
    conn = pymssql.connect(
        server=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        autocommit=True
    )
    cursor = conn.cursor()

    script_path = "scripts/sql/04_create_stored_procedures.sql"
    with open(script_path, "r") as f:
        sql_script = f.read()

    batches = sql_script.split("GO")
    for batch in batches:
        lines = []
        for line in batch.splitlines():
            line_str = line.strip()
            if line_str and not line_str.startswith("--"):
                lines.append(line)
        
        batch_text = "\n".join(lines).strip()
        if batch_text and not batch_text.upper().startswith("USE "):
            try:
                cursor.execute(batch_text)
            except Exception as e:
                print(f"Error executing batch:\n{batch_text[:100]}...\nException: {e}")
                raise e

    print("\n--- Stored Procedures Deployment Verification ---")
    expected_sps = [
        "sp_detect_duplicates",
        "sp_validate_customers",
        "sp_validate_accounts",
        "sp_validate_transactions",
        "sp_reconcile_migration",
        "sp_generate_migration_summary"
    ]

    cursor.execute("SELECT ROUTINE_NAME FROM INFORMATION_SCHEMA.ROUTINES WHERE ROUTINE_TYPE = 'PROCEDURE';")
    existing_sps = [row[0] for row in cursor.fetchall()]

    for sp in expected_sps:
        if sp in existing_sps:
            print(f"  • Stored Procedure '{sp}': DEPLOYED & VERIFIED ✅")
        else:
            print(f"  • ERROR: Stored Procedure '{sp}' MISSING ❌")

    conn.close()
    return existing_sps

if __name__ == "__main__":
    deploy_stored_procedures()
