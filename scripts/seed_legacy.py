import os
import pymssql
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "1433"))
DB_USER = os.getenv("DB_USER", "sa")
DB_PASSWORD = os.getenv("DB_PASSWORD", "BankMigrate123!")
DB_NAME = os.getenv("DB_LEGACY_NAME", "BankMigrate_Legacy")

def seed_legacy_database():
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

    # Step 1: Drop existing legacy tables
    tables = [
        "Transactions_Legacy",
        "Loans_Legacy",
        "Beneficiaries_Legacy",
        "Accounts_Legacy",
        "Customers_Legacy",
        "Addresses_Legacy"
    ]
    for table in tables:
        cursor.execute(f"IF OBJECT_ID('{table}', 'U') IS NOT NULL DROP TABLE {table};")

    # Step 2: Create Legacy Tables
    cursor.execute("""
    CREATE TABLE Addresses_Legacy (
        address_id NVARCHAR(50) NULL,
        street_address NVARCHAR(255) NULL,
        city NVARCHAR(100) NULL,
        state NVARCHAR(100) NULL,
        postal_code NVARCHAR(20) NULL,
        country NVARCHAR(100) NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE Customers_Legacy (
        customer_id NVARCHAR(50) NULL,
        customer_name NVARCHAR(200) NULL,
        dob NVARCHAR(50) NULL,
        phone NVARCHAR(50) NULL,
        email NVARCHAR(200) NULL,
        address_id NVARCHAR(50) NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE Accounts_Legacy (
        account_id NVARCHAR(50) NULL,
        customer_id NVARCHAR(50) NULL,
        account_type NVARCHAR(50) NULL,
        balance DECIMAL(18, 2) NULL,
        opened_date NVARCHAR(50) NULL,
        status NVARCHAR(50) NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE Transactions_Legacy (
        transaction_id NVARCHAR(50) NULL,
        account_id NVARCHAR(50) NULL,
        transaction_type NVARCHAR(50) NULL,
        amount DECIMAL(18, 2) NULL,
        transaction_date NVARCHAR(50) NULL,
        description NVARCHAR(255) NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE Loans_Legacy (
        loan_id NVARCHAR(50) NULL,
        account_id NVARCHAR(50) NULL,
        loan_amount DECIMAL(18, 2) NULL,
        interest_rate DECIMAL(5, 2) NULL,
        term_months INT NULL,
        start_date NVARCHAR(50) NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE Beneficiaries_Legacy (
        beneficiary_id NVARCHAR(50) NULL,
        customer_id NVARCHAR(50) NULL,
        beneficiary_name NVARCHAR(200) NULL,
        account_number NVARCHAR(50) NULL,
        routing_code NVARCHAR(50) NULL
    );
    """)

    # Step 3: Read and execute seed SQL file
    script_path = "scripts/sql/02_create_seed_legacy.sql"
    with open(script_path, "r") as f:
        sql_script = f.read()

    for line in sql_script.splitlines():
        line_str = line.strip()
        if line_str.startswith("INSERT INTO"):
            cursor.execute(line_str)

    print("\n--- Legacy Database Seeding Verification ---")
    verification_results = {}
    for table in reversed(tables):
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        verification_results[table] = count
        print(f"Table '{table}': {count} total rows seeded.")

    conn.close()
    return verification_results

if __name__ == "__main__":
    seed_legacy_database()
