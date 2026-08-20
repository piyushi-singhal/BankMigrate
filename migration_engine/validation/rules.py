"""
Validation rules catalog for BankMigrate validation engine.
"""

VALIDATION_RULES = {
    # Customer Rules
    "CUSTOMER_001": {
        "entity": "Customer",
        "severity": "ERROR",
        "description": "Customer ID is required and cannot be NULL or empty."
    },
    "CUSTOMER_002": {
        "entity": "Customer",
        "severity": "ERROR",
        "description": "Duplicate customer record detected based on natural key."
    },
    "CUSTOMER_003": {
        "entity": "Customer",
        "severity": "WARNING",
        "description": "Invalid phone number format."
    },
    "CUSTOMER_004": {
        "entity": "Customer",
        "severity": "ERROR",
        "description": "Invalid email address format."
    },
    "CUSTOMER_005": {
        "entity": "Customer",
        "severity": "ERROR",
        "description": "Invalid date of birth format or value."
    },

    # Account Rules
    "ACCOUNT_001": {
        "entity": "Account",
        "severity": "ERROR",
        "description": "Account ID is required."
    },
    "ACCOUNT_002": {
        "entity": "Account",
        "severity": "ERROR",
        "description": "Referenced customer ID does not exist in valid Customers."
    },
    "ACCOUNT_003": {
        "entity": "Account",
        "severity": "ERROR",
        "description": "Invalid account type."
    },
    "ACCOUNT_004": {
        "entity": "Account",
        "severity": "ERROR",
        "description": "Invalid balance (negative balance on savings/checking)."
    },

    # Transaction Rules
    "TXN_001": {
        "entity": "Transaction",
        "severity": "ERROR",
        "description": "Transaction ID is required."
    },
    "TXN_002": {
        "entity": "Transaction",
        "severity": "ERROR",
        "description": "Referenced account ID does not exist in valid Accounts."
    },
    "TXN_003": {
        "entity": "Transaction",
        "severity": "ERROR",
        "description": "Invalid transaction amount (must be positive)."
    },
    "TXN_004": {
        "entity": "Transaction",
        "severity": "ERROR",
        "description": "Invalid transaction date format."
    },
    "TXN_005": {
        "entity": "Transaction",
        "severity": "ERROR",
        "description": "Duplicate transaction row detected."
    }
}
