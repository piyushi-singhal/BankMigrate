-- 01_create_databases.sql
-- Milestone 1: Provision SQL Server and create legacy and target databases

IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'BankMigrate_Legacy')
BEGIN
    CREATE DATABASE BankMigrate_Legacy;
    PRINT 'Database BankMigrate_Legacy created successfully.';
END
ELSE
BEGIN
    PRINT 'Database BankMigrate_Legacy already exists.';
END
GO

IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'BankMigrate_Target')
BEGIN
    CREATE DATABASE BankMigrate_Target;
    PRINT 'Database BankMigrate_Target created successfully.';
END
ELSE
BEGIN
    PRINT 'Database BankMigrate_Target already exists.';
END
GO
