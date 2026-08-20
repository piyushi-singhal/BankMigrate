import os
import pymssql
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "1433"))
DB_USER = os.getenv("DB_USER", "sa")
DB_PASSWORD = os.getenv("DB_PASSWORD", "BankMigrate123!")
DB_NAME = os.getenv("DB_TARGET_NAME", "BankMigrate_Target")

def create_target_schema():
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

    script_path = "scripts/sql/03_create_target_schema.sql"
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

    print("\n--- Target Database Schema Verification ---")
    expected_tables = [
        "Addresses",
        "Customers",
        "Accounts",
        "Transactions",
        "Loans",
        "Beneficiaries",
        "MigrationRuns",
        "MigrationExceptions",
        "MigrationAudit"
    ]

    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE';")
    existing_tables = [row[0] for row in cursor.fetchall()]

    for table in expected_tables:
        if table in existing_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]
            print(f"Table '{table}': CREATED (Rows: {count})")
        else:
            print(f"ERROR: Table '{table}' MISSING from {DB_NAME}!")

    conn.close()
    return existing_tables

if __name__ == "__main__":
    create_target_schema()
