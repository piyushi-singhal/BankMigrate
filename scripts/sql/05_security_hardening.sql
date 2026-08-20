-- 05_security_hardening.sql
-- Milestone 17: Security Hardening & Least-Privilege Database Access

USE BankMigrate_Target;
GO

-- Create Restricted Application User & Role for BankMigrate
IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = 'bankmigrate_app_role')
BEGIN
    CREATE ROLE bankmigrate_app_role;
END;
GO

-- Grant Least-Privilege Permissions to bankmigrate_app_role
GRANT SELECT, INSERT, UPDATE, DELETE ON SCHEMA::dbo TO bankmigrate_app_role;
GRANT EXECUTE ON SCHEMA::dbo TO bankmigrate_app_role;
GO

-- Deny DDL drop and alter server permissions
DENY ALTER TO bankmigrate_app_role;
GO

PRINT 'Security Hardening: bankmigrate_app_role created with least-privilege DML and EXECUTE permissions.';
GO
