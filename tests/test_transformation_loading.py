import pytest
from migration_engine.extraction.extractor import extract_legacy_data
from migration_engine.validation.validator import validate_all_entities
from migration_engine.transformation.transformer import transform_all_entities
from migration_engine.loading.loader import load_transformed_data
from migration_engine.config.settings import get_target_connection

def test_transformation_and_loading():
    raw_data = extract_legacy_data()
    valid_data, _ = validate_all_entities(raw_data)
    transformed_data = transform_all_entities(valid_data)
    
    # Verify Title Case and Email lowering
    cust_df = transformed_data["Customers"]
    assert cust_df["full_name"].iloc[0] == "John Smith"
    assert cust_df["email"].iloc[0] == "john.smith@gmail.com"
    
    # Verify Bulk Loading
    counts = load_transformed_data(transformed_data, clear_first=True)
    assert counts["Addresses"] == 5
    assert counts["Customers"] == 7
    assert counts["Accounts"] == 6
    assert counts["Transactions"] == 7
    assert counts["Loans"] == 2
    assert counts["Beneficiaries"] == 2
    
    # Query SQL Server directly to confirm counts
    conn = get_target_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Customers;")
    db_cust_count = cursor.fetchone()[0]
    assert db_cust_count == 7
    conn.close()
