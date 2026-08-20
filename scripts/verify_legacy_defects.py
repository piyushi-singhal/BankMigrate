import os
import pymssql
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "1433"))
DB_USER = os.getenv("DB_USER", "sa")
DB_PASSWORD = os.getenv("DB_PASSWORD", "BankMigrate123!")
DB_NAME = os.getenv("DB_LEGACY_NAME", "BankMigrate_Legacy")

def verify_legacy_defects():
    conn = pymssql.connect(
        server=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        autocommit=True
    )
    cursor = conn.cursor()

    print("=================================================================")
    print("      MILESTONE 2: LEGACY DATA QUALITY DEFECTS VERIFICATION     ")
    print("=================================================================\n")

    # Defect 1: Duplicate Customers (C001 vs C019)
    cursor.execute("SELECT customer_id, customer_name, dob, email FROM Customers_Legacy WHERE customer_id IN ('C001', 'C019');")
    print("[DEFECT 1 - CUSTOMER_002] Duplicate Customers:")
    for row in cursor.fetchall():
        print("  -", row)

    # Defect 2: Missing Mandatory customer_id (CUSTOMER_001)
    cursor.execute("SELECT customer_id, customer_name, email FROM Customers_Legacy WHERE customer_id IS NULL;")
    print("\n[DEFECT 2 - CUSTOMER_001] Missing Mandatory customer_id:")
    for row in cursor.fetchall():
        print("  -", row)

    # Defect 3: Invalid Email Format (CUSTOMER_004)
    cursor.execute("SELECT customer_id, customer_name, email FROM Customers_Legacy WHERE email LIKE '%_at_%';")
    print("\n[DEFECT 3 - CUSTOMER_004] Invalid Email Format:")
    for row in cursor.fetchall():
        print("  -", row)

    # Defect 4: Invalid Date of Birth (CUSTOMER_005)
    cursor.execute("SELECT customer_id, customer_name, dob FROM Customers_Legacy WHERE dob = '31/02/1999';")
    print("\n[DEFECT 4 - CUSTOMER_005] Invalid Date of Birth (31/02/1999):")
    for row in cursor.fetchall():
        print("  -", row)

    # Defect 5: Invalid Negative Balance (ACCOUNT_004)
    cursor.execute("SELECT account_id, customer_id, account_type, balance FROM Accounts_Legacy WHERE balance < 0;")
    print("\n[DEFECT 5 - ACCOUNT_004] Invalid Negative Balance on Savings:")
    for row in cursor.fetchall():
        print("  -", row)

    # Defect 6: Invalid Foreign Key in Accounts (ACCOUNT_002)
    cursor.execute("SELECT account_id, customer_id, account_type FROM Accounts_Legacy WHERE customer_id = 'C999';")
    print("\n[DEFECT 6 - ACCOUNT_002] Invalid Foreign Key (Nonexistent Customer C999):")
    for row in cursor.fetchall():
        print("  -", row)

    # Defect 7: Duplicate Transactions (TXN_005)
    cursor.execute("SELECT transaction_id, account_id, amount, COUNT(*) FROM Transactions_Legacy WHERE transaction_id = 'TXN-1005' GROUP BY transaction_id, account_id, amount;")
    print("\n[DEFECT 7 - TXN_005] Duplicate Transaction:")
    for row in cursor.fetchall():
        print(f"  - Transaction ID {row[0]} appears {row[3]} times.")

    # Defect 8: Invalid Foreign Key in Transactions (TXN_002 - Orphan Transaction)
    cursor.execute("SELECT transaction_id, account_id, amount, description FROM Transactions_Legacy WHERE account_id = 'A999999';")
    print("\n[DEFECT 8 - TXN_002] Orphan Transaction (Nonexistent Account A999999):")
    for row in cursor.fetchall():
        print("  -", row)

    # Defect 9: Invalid Transaction Amount (TXN_003)
    cursor.execute("SELECT transaction_id, account_id, amount FROM Transactions_Legacy WHERE amount < 0;")
    print("\n[DEFECT 9 - TXN_003] Invalid Negative Transaction Amount:")
    for row in cursor.fetchall():
        print("  -", row)

    conn.close()

if __name__ == "__main__":
    verify_legacy_defects()
