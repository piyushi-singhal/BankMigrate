"""
Failure Simulation Module for BankMigrate Pipeline (Milestone 16)
Supports injecting:
1. NETWORK_DROP: Connection failure during database operations.
2. DIRTY_INPUT: Unexpected data type corruption.
3. LOCKED_TABLE: Database lock timeout.
"""

class MigrationFailureException(Exception):
    """Custom exception raised when a failure scenario is injected."""
    pass

def inject_failure_if_requested(failure_type: str, stage: str):
    """
    Checks failure_type and raises simulated exception if matching stage.
    """
    if not failure_type:
        return

    failure_type = failure_type.upper()
    stage = stage.lower()

    if failure_type == "NETWORK_DROP" and stage == "extraction":
        raise MigrationFailureException("SIMULATED ERROR: Network connection dropped during legacy data extraction.")

    if failure_type == "LOCKED_TABLE" and stage == "loading":
        raise MigrationFailureException("SIMULATED ERROR: SQL Server table lock timeout on target database table 'Accounts'.")

    if failure_type == "DIRTY_INPUT" and stage == "validation":
        raise MigrationFailureException("SIMULATED ERROR: Dirty binary input corrupting validation stage.")
