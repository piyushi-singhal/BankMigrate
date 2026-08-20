import pytest
from migration_engine.extraction.extractor import extract_legacy_data
from migration_engine.validation.validator import validate_all_entities

def test_validation_rule_isolation():
    raw_data = extract_legacy_data()
    valid_data, exceptions = validate_all_entities(raw_data)
    
    # 11 source customers - 4 invalid = 7 valid customers
    assert len(valid_data["Customers"]) == 7
    
    # 8 source accounts - 2 invalid = 6 valid accounts
    assert len(valid_data["Accounts"]) == 6
    
    # 10 source transactions - 3 invalid = 7 valid transactions
    assert len(valid_data["Transactions"]) == 7
    
    # Total isolated exceptions must equal exactly 9
    assert len(exceptions) == 9
    
    rule_ids = set(ex["rule_id"] for ex in exceptions)
    expected_rules = {
        "CUSTOMER_001", "CUSTOMER_002", "CUSTOMER_004", "CUSTOMER_005",
        "ACCOUNT_002", "ACCOUNT_004",
        "TXN_002", "TXN_003", "TXN_005"
    }
    assert rule_ids == expected_rules
