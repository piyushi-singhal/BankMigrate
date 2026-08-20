import os
import time
import pymssql
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "1433"))
DB_USER = os.getenv("DB_USER", "sa")
DB_PASSWORD = os.getenv("DB_PASSWORD", "BankMigrate123!")

def wait_for_sql_server():
    print(f"Connecting to SQL Server at {DB_HOST}:{DB_PORT} as {DB_USER}...")
    max_retries = 30
    for i in range(max_retries):
        try:
            conn = pymssql.connect(
                server=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                autocommit=True
            )
            conn.close()
            print("SQL Server is ready!")
            return True
        except Exception as e:
            print(f"Waiting for SQL Server... ({i+1}/{max_retries}) - {e}")
            time.sleep(2)
    return False

def create_databases():
    conn = pymssql.connect(
        server=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        autocommit=True
    )
    cursor = conn.cursor()
    
    with open("scripts/sql/01_create_databases.sql", "r") as f:
        sql_script = f.read()

    batches = sql_script.split("GO")
    for batch in batches:
        clean_batch = batch.strip()
        if clean_batch:
            cursor.execute(clean_batch)
            print(f"Executed batch: {clean_batch[:40]}...")

    # Verify database creation
    cursor.execute("SELECT name FROM sys.databases WHERE name IN ('BankMigrate_Legacy', 'BankMigrate_Target');")
    databases = cursor.fetchall()
    print("Created Databases:", [db[0] for db in databases])
    conn.close()
    return [db[0] for db in databases]

if __name__ == "__main__":
    if wait_for_sql_server():
        create_databases()
    else:
        print("Error: SQL Server did not become ready in time.")
        exit(1)
