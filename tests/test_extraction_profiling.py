import pytest
from migration_engine.extraction.extractor import extract_legacy_data
from migration_engine.profiling.profiler import profile_all_tables

def test_extract_legacy_data():
    raw_data = extract_legacy_data()
    assert isinstance(raw_data, dict)
    expected_tables = {
        "Addresses_Legacy",
        "Customers_Legacy",
        "Accounts_Legacy",
        "Transactions_Legacy",
        "Loans_Legacy",
        "Beneficiaries_Legacy"
    }
    assert set(raw_data.keys()) == expected_tables
    
    # Check non-empty DataFrames extracted
    assert len(raw_data["Customers_Legacy"]) == 11
    assert len(raw_data["Accounts_Legacy"]) == 8
    assert len(raw_data["Transactions_Legacy"]) == 10

def test_profile_legacy_data():
    raw_data = extract_legacy_data()
    profiles = profile_all_tables(raw_data)
    assert isinstance(profiles, dict)
    assert profiles["Customers_Legacy"]["total_rows"] == 11
    assert profiles["Transactions_Legacy"]["duplicate_rows"] == 1
