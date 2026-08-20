-- 04_create_stored_procedures.sql
-- Milestone 10: T-SQL Stored Procedure Layer for BankMigrate

USE BankMigrate_Target;
GO

-- 1. sp_detect_duplicates
IF OBJECT_ID('sp_detect_duplicates', 'P') IS NOT NULL DROP PROCEDURE sp_detect_duplicates;
GO
CREATE PROCEDURE sp_detect_duplicates
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        -- CTE using Window Function ROW_NUMBER() to detect duplicate customers
        WITH CustomerDuplicates AS (
            SELECT 
                customer_id,
                customer_name,
                dob,
                ROW_NUMBER() OVER (
                    PARTITION BY LOWER(TRIM(customer_name)), dob 
                    ORDER BY customer_id
                ) AS row_num
            FROM BankMigrate_Legacy.dbo.Customers_Legacy
            WHERE customer_id IS NOT NULL
        )
        SELECT customer_id, customer_name, dob, row_num
        FROM CustomerDuplicates
        WHERE row_num > 1;

        -- CTE using Window Function ROW_NUMBER() to detect duplicate transactions
        WITH TransactionDuplicates AS (
            SELECT 
                transaction_id,
                account_id,
                amount,
                ROW_NUMBER() OVER (
                    PARTITION BY transaction_id 
                    ORDER BY transaction_date
                ) AS row_num
            FROM BankMigrate_Legacy.dbo.Transactions_Legacy
            WHERE transaction_id IS NOT NULL
        )
        SELECT transaction_id, account_id, amount, row_num
        FROM TransactionDuplicates
        WHERE row_num > 1;
    END TRY
    BEGIN CATCH
        DECLARE @ErrMsg NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR(@ErrMsg, 16, 1);
    END CATCH
END;
GO

-- 2. sp_validate_customers
IF OBJECT_ID('sp_validate_customers', 'P') IS NOT NULL DROP PROCEDURE sp_validate_customers;
GO
CREATE PROCEDURE sp_validate_customers
    @RunId NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRANSACTION;
    BEGIN TRY
        -- Temp Table to store detected customer exceptions
        CREATE TABLE #CustExceptions (
            run_id NVARCHAR(50),
            entity_type NVARCHAR(50),
            record_id NVARCHAR(50),
            rule_id NVARCHAR(50),
            severity NVARCHAR(20),
            error_message NVARCHAR(MAX),
            source_data NVARCHAR(MAX)
        );

        -- CUSTOMER_001: Missing Customer ID
        INSERT INTO #CustExceptions (run_id, entity_type, record_id, rule_id, severity, error_message, source_data)
        SELECT 
            @RunId, 'Customer', NULL, 'CUSTOMER_001', 'ERROR', 
            'Customer ID is required and cannot be NULL or empty.',
            (SELECT c.customer_name, c.dob, c.phone, c.email FOR JSON PATH, WITHOUT_ARRAY_WRAPPER)
        FROM BankMigrate_Legacy.dbo.Customers_Legacy c
        WHERE c.customer_id IS NULL OR TRIM(c.customer_id) = '';

        -- CUSTOMER_002: Duplicate Customer (using Window Function)
        WITH DupCustCTE AS (
            SELECT customer_id, customer_name, dob, phone, email,
                   ROW_NUMBER() OVER (PARTITION BY LOWER(TRIM(customer_name)), dob ORDER BY customer_id) AS rn
            FROM BankMigrate_Legacy.dbo.Customers_Legacy
            WHERE customer_id IS NOT NULL
        )
        INSERT INTO #CustExceptions (run_id, entity_type, record_id, rule_id, severity, error_message, source_data)
        SELECT 
            @RunId, 'Customer', customer_id, 'CUSTOMER_002', 'ERROR',
            'Duplicate customer record detected.',
            (SELECT customer_id, customer_name, dob, phone, email FOR JSON PATH, WITHOUT_ARRAY_WRAPPER)
        FROM DupCustCTE
        WHERE rn > 1;

        -- CUSTOMER_004: Invalid Email Format
        INSERT INTO #CustExceptions (run_id, entity_type, record_id, rule_id, severity, error_message, source_data)
        SELECT 
            @RunId, 'Customer', customer_id, 'CUSTOMER_004', 'ERROR',
            'Invalid email format: ' + ISNULL(email, ''),
            (SELECT customer_id, customer_name, email FOR JSON PATH, WITHOUT_ARRAY_WRAPPER)
        FROM BankMigrate_Legacy.dbo.Customers_Legacy
        WHERE email IS NOT NULL AND email NOT LIKE '%@%.%';

        -- CUSTOMER_005: Invalid Date of Birth (e.g. 31/02/1999)
        INSERT INTO #CustExceptions (run_id, entity_type, record_id, rule_id, severity, error_message, source_data)
        SELECT 
            @RunId, 'Customer', customer_id, 'CUSTOMER_005', 'ERROR',
            'Invalid date of birth: ' + ISNULL(dob, ''),
            (SELECT customer_id, customer_name, dob FOR JSON PATH, WITHOUT_ARRAY_WRAPPER)
        FROM BankMigrate_Legacy.dbo.Customers_Legacy
        WHERE dob LIKE '31/02/%';

        -- Insert from Temp Table into MigrationExceptions
        INSERT INTO MigrationExceptions (run_id, entity_type, record_id, rule_id, severity, error_message, source_data, status)
        SELECT run_id, entity_type, record_id, rule_id, severity, error_message, source_data, 'OPEN'
        FROM #CustExceptions;

        DROP TABLE #CustExceptions;
        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        DECLARE @ErrMsgCust NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR(@ErrMsgCust, 16, 1);
    END CATCH
END;
GO

-- 3. sp_validate_accounts
IF OBJECT_ID('sp_validate_accounts', 'P') IS NOT NULL DROP PROCEDURE sp_validate_accounts;
GO
CREATE PROCEDURE sp_validate_accounts
    @RunId NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRANSACTION;
    BEGIN TRY
        -- ACCOUNT_002: Customer FK Validation Check
        INSERT INTO MigrationExceptions (run_id, entity_type, record_id, rule_id, severity, error_message, source_data, status)
        SELECT 
            @RunId, 'Account', a.account_id, 'ACCOUNT_002', 'ERROR',
            'Referenced customer ' + ISNULL(a.customer_id, 'NULL') + ' does not exist in target Customers table.',
            (SELECT a.account_id, a.customer_id, a.account_type, a.balance FOR JSON PATH, WITHOUT_ARRAY_WRAPPER),
            'OPEN'
        FROM BankMigrate_Legacy.dbo.Accounts_Legacy a
        LEFT JOIN Customers c ON a.customer_id = c.customer_id
        WHERE c.customer_id IS NULL;

        -- ACCOUNT_004: Invalid Negative Balance
        INSERT INTO MigrationExceptions (run_id, entity_type, record_id, rule_id, severity, error_message, source_data, status)
        SELECT 
            @RunId, 'Account', a.account_id, 'ACCOUNT_004', 'ERROR',
            'Invalid negative balance (' + CAST(a.balance AS NVARCHAR(50)) + ') on ' + a.account_type + ' account.',
            (SELECT a.account_id, a.customer_id, a.account_type, a.balance FOR JSON PATH, WITHOUT_ARRAY_WRAPPER),
            'OPEN'
        FROM BankMigrate_Legacy.dbo.Accounts_Legacy a
        WHERE UPPER(a.account_type) IN ('SAVINGS', 'CHECKING') AND a.balance < 0;

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        DECLARE @ErrMsgAcct NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR(@ErrMsgAcct, 16, 1);
    END CATCH
END;
GO

-- 4. sp_validate_transactions
IF OBJECT_ID('sp_validate_transactions', 'P') IS NOT NULL DROP PROCEDURE sp_validate_transactions;
GO
CREATE PROCEDURE sp_validate_transactions
    @RunId NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRANSACTION;
    BEGIN TRY
        -- TXN_002: Account FK Validation Check
        INSERT INTO MigrationExceptions (run_id, entity_type, record_id, rule_id, severity, error_message, source_data, status)
        SELECT 
            @RunId, 'Transaction', t.transaction_id, 'TXN_002', 'ERROR',
            'Referenced account ' + ISNULL(t.account_id, 'NULL') + ' does not exist in target Accounts table.',
            (SELECT t.transaction_id, t.account_id, t.amount, t.transaction_date FOR JSON PATH, WITHOUT_ARRAY_WRAPPER),
            'OPEN'
        FROM BankMigrate_Legacy.dbo.Transactions_Legacy t
        LEFT JOIN Accounts a ON t.account_id = a.account_id
        WHERE a.account_id IS NULL;

        -- TXN_003: Invalid Transaction Amount (Negative Amount)
        INSERT INTO MigrationExceptions (run_id, entity_type, record_id, rule_id, severity, error_message, source_data, status)
        SELECT 
            @RunId, 'Transaction', t.transaction_id, 'TXN_003', 'ERROR',
            'Invalid transaction amount: ' + CAST(t.amount AS NVARCHAR(50)),
            (SELECT t.transaction_id, t.account_id, t.amount FOR JSON PATH, WITHOUT_ARRAY_WRAPPER),
            'OPEN'
        FROM BankMigrate_Legacy.dbo.Transactions_Legacy t
        WHERE t.amount <= 0;

        -- TXN_005: Duplicate Transaction (Window Function)
        WITH DupTxnCTE AS (
            SELECT transaction_id, account_id, amount, transaction_date,
                   ROW_NUMBER() OVER (PARTITION BY transaction_id ORDER BY transaction_date) AS rn
            FROM BankMigrate_Legacy.dbo.Transactions_Legacy
            WHERE transaction_id IS NOT NULL
        )
        INSERT INTO MigrationExceptions (run_id, entity_type, record_id, rule_id, severity, error_message, source_data, status)
        SELECT 
            @RunId, 'Transaction', transaction_id, 'TXN_005', 'ERROR',
            'Duplicate transaction ID ' + transaction_id + ' detected.',
            (SELECT transaction_id, account_id, amount FOR JSON PATH, WITHOUT_ARRAY_WRAPPER),
            'OPEN'
        FROM DupTxnCTE
        WHERE rn > 1;

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        DECLARE @ErrMsgTxn NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR(@ErrMsgTxn, 16, 1);
    END CATCH
END;
GO

-- 5. sp_reconcile_migration
IF OBJECT_ID('sp_reconcile_migration', 'P') IS NOT NULL DROP PROCEDURE sp_reconcile_migration;
GO
CREATE PROCEDURE sp_reconcile_migration
    @RunId NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        DECLARE @SrcTxnSum DECIMAL(18,2), @TgtTxnSum DECIMAL(18,2), @RejTxnSum DECIMAL(18,2);

        -- Total Source Transaction Amount
        SELECT @SrcTxnSum = ISNULL(SUM(amount), 0) FROM BankMigrate_Legacy.dbo.Transactions_Legacy;

        -- Total Target Transaction Amount
        SELECT @TgtTxnSum = ISNULL(SUM(amount), 0) FROM Transactions;

        -- Total Rejected Transaction Amount
        SELECT @RejTxnSum = ISNULL(SUM(CAST(JSON_VALUE(source_data, '$.amount') AS DECIMAL(18,2))), 0)
        FROM MigrationExceptions
        WHERE run_id = @RunId AND entity_type = 'Transaction' AND rule_id IN ('TXN_002', 'TXN_003');

        SELECT 
            @RunId AS run_id,
            (SELECT source_records FROM MigrationRuns WHERE run_id = @RunId) AS source_records,
            (SELECT loaded_records FROM MigrationRuns WHERE run_id = @RunId) AS loaded_records,
            (SELECT rejected_records FROM MigrationRuns WHERE run_id = @RunId) AS rejected_records,
            @SrcTxnSum AS source_txn_amount,
            @TgtTxnSum AS target_txn_amount,
            @RejTxnSum AS rejected_txn_amount,
            CASE 
                WHEN @SrcTxnSum = (@TgtTxnSum + @RejTxnSum) THEN 'BALANCED'
                ELSE 'DISCREPANCY_DETECTED'
            END AS reconciliation_status;
    END TRY
    BEGIN CATCH
        DECLARE @ErrMsgRec NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR(@ErrMsgRec, 16, 1);
    END CATCH
END;
GO

-- 6. sp_generate_migration_summary
IF OBJECT_ID('sp_generate_migration_summary', 'P') IS NOT NULL DROP PROCEDURE sp_generate_migration_summary;
GO
CREATE PROCEDURE sp_generate_migration_summary
    @RunId NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        SELECT 
            r.run_id,
            r.started_at,
            r.completed_at,
            r.status AS run_status,
            r.source_records,
            r.validated_records,
            r.transformed_records,
            r.loaded_records,
            r.rejected_records,
            (SELECT COUNT(*) FROM MigrationExceptions WHERE run_id = @RunId) AS total_exceptions,
            (SELECT COUNT(*) FROM MigrationAudit WHERE run_id = @RunId) AS total_audit_entries
        FROM MigrationRuns r
        WHERE r.run_id = @RunId;
    END TRY
    BEGIN CATCH
        DECLARE @ErrMsgSum NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR(@ErrMsgSum, 16, 1);
    END CATCH
END;
GO
