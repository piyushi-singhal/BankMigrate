-- 02_create_seed_legacy.sql
-- Milestone 2: Create and seed legacy schema (BankMigrate_Legacy) with intentional data-quality defects

USE BankMigrate_Legacy;
GO

-- Drop tables if they already exist
IF OBJECT_ID('Transactions_Legacy', 'U') IS NOT NULL DROP TABLE Transactions_Legacy;
IF OBJECT_ID('Loans_Legacy', 'U') IS NOT NULL DROP TABLE Loans_Legacy;
IF OBJECT_ID('Beneficiaries_Legacy', 'U') IS NOT NULL DROP TABLE Beneficiaries_Legacy;
IF OBJECT_ID('Accounts_Legacy', 'U') IS NOT NULL DROP TABLE Accounts_Legacy;
IF OBJECT_ID('Customers_Legacy', 'U') IS NOT NULL DROP TABLE Customers_Legacy;
IF OBJECT_ID('Addresses_Legacy', 'U') IS NOT NULL DROP TABLE Addresses_Legacy;
GO

-- 1. Addresses_Legacy
CREATE TABLE Addresses_Legacy (
    address_id NVARCHAR(50) NULL,
    street_address NVARCHAR(255) NULL,
    city NVARCHAR(100) NULL,
    state NVARCHAR(100) NULL,
    postal_code NVARCHAR(20) NULL,
    country NVARCHAR(100) NULL
);

-- 2. Customers_Legacy
CREATE TABLE Customers_Legacy (
    customer_id NVARCHAR(50) NULL,
    customer_name NVARCHAR(200) NULL,
    dob NVARCHAR(50) NULL,
    phone NVARCHAR(50) NULL,
    email NVARCHAR(200) NULL,
    address_id NVARCHAR(50) NULL
);

-- 3. Accounts_Legacy
CREATE TABLE Accounts_Legacy (
    account_id NVARCHAR(50) NULL,
    customer_id NVARCHAR(50) NULL,
    account_type NVARCHAR(50) NULL,
    balance DECIMAL(18, 2) NULL,
    opened_date NVARCHAR(50) NULL,
    status NVARCHAR(50) NULL
);

-- 4. Transactions_Legacy
CREATE TABLE Transactions_Legacy (
    transaction_id NVARCHAR(50) NULL,
    account_id NVARCHAR(50) NULL,
    transaction_type NVARCHAR(50) NULL,
    amount DECIMAL(18, 2) NULL,
    transaction_date NVARCHAR(50) NULL,
    description NVARCHAR(255) NULL
);

-- 5. Loans_Legacy
CREATE TABLE Loans_Legacy (
    loan_id NVARCHAR(50) NULL,
    account_id NVARCHAR(50) NULL,
    loan_amount DECIMAL(18, 2) NULL,
    interest_rate DECIMAL(5, 2) NULL,
    term_months INT NULL,
    start_date NVARCHAR(50) NULL
);

-- 6. Beneficiaries_Legacy
CREATE TABLE Beneficiaries_Legacy (
    beneficiary_id NVARCHAR(50) NULL,
    customer_id NVARCHAR(50) NULL,
    beneficiary_name NVARCHAR(200) NULL,
    account_number NVARCHAR(50) NULL,
    routing_code NVARCHAR(50) NULL
);
GO

-- 1. Addresses_Legacy Seed Data
INSERT INTO Addresses_Legacy (address_id, street_address, city, state, postal_code, country) VALUES ('ADDR001', '123 Financial Way', 'New York', 'NY', '10001', 'USA');
INSERT INTO Addresses_Legacy (address_id, street_address, city, state, postal_code, country) VALUES ('ADDR002', '456 Wall Street', 'New York', 'NY', '10005', 'USA');
INSERT INTO Addresses_Legacy (address_id, street_address, city, state, postal_code, country) VALUES ('ADDR003', '789 Market Street', 'San Francisco', 'CA', '94103', 'USA');
INSERT INTO Addresses_Legacy (address_id, street_address, city, state, postal_code, country) VALUES ('ADDR004', '101 Bay Street', 'Toronto', 'ON', 'M5J 2R8', 'Canada');
INSERT INTO Addresses_Legacy (address_id, street_address, city, state, postal_code, country) VALUES ('ADDR005', '12 Lombard Street', 'London', 'Greater London', 'EC3V 9AA', 'UK');
GO

-- 2. Customers_Legacy Seed Data
INSERT INTO Customers_Legacy (customer_id, customer_name, dob, phone, email, address_id) VALUES ('C001', ' john smith ', '1985-05-15', '+91-9876543210', ' john.smith@gmail.com ', 'ADDR001');
INSERT INTO Customers_Legacy (customer_id, customer_name, dob, phone, email, address_id) VALUES ('C002', 'Alice Cooper', '1990-11-20', '09876543210', 'alice.c@yahoo.com', 'ADDR002');
INSERT INTO Customers_Legacy (customer_id, customer_name, dob, phone, email, address_id) VALUES ('C003', 'Robert Plant', '1978-03-04', '98765 43210', 'robert.plant@led.org', 'ADDR003');
INSERT INTO Customers_Legacy (customer_id, customer_name, dob, phone, email, address_id) VALUES ('C004', 'David Gilmour', '1965-07-12', '9876543210', 'david@floyd.co.uk', 'ADDR004');
INSERT INTO Customers_Legacy (customer_id, customer_name, dob, phone, email, address_id) VALUES ('C005', 'Freddie Mercury', '1972-09-05', '555-1234', 'freddie@queen.com', 'ADDR005');
INSERT INTO Customers_Legacy (customer_id, customer_name, dob, phone, email, address_id) VALUES ('C008', 'Bruce Wayne', '1980-02-19', '9876577777', 'bruce@gotham.org', 'ADDR001');
INSERT INTO Customers_Legacy (customer_id, customer_name, dob, phone, email, address_id) VALUES ('C009', 'Clark Kent', '1982-06-18', '9876566666', 'clark@dailyplanet.com', 'ADDR002');

-- DEFECT 1: Duplicate customer (C019 is duplicate of C001 'John Smith')
INSERT INTO Customers_Legacy (customer_id, customer_name, dob, phone, email, address_id) VALUES ('C019', 'JOHN SMITH', '1985-05-15', '09876543210', 'JOHN.SMITH@GMAIL.COM', 'ADDR001');

-- DEFECT 2: Missing mandatory customer_id (CUSTOMER_001 failure)
INSERT INTO Customers_Legacy (customer_id, customer_name, dob, phone, email, address_id) VALUES (NULL, 'Jane Doe', '1992-08-10', '9876512345', 'jane.doe@example.com', 'ADDR002');

-- DEFECT 3: Invalid email format (CUSTOMER_004 failure)
INSERT INTO Customers_Legacy (customer_id, customer_name, dob, phone, email, address_id) VALUES ('C006', 'Charlie Brown', '1988-12-01', '9876599999', 'charlie_brown_at_domain.com', 'ADDR003');

-- DEFECT 4: Invalid date of birth (31/02/1999 does not exist - CUSTOMER_005 failure)
INSERT INTO Customers_Legacy (customer_id, customer_name, dob, phone, email, address_id) VALUES ('C007', 'Diana Prince', '31/02/1999', '9876588888', 'diana@wonder.com', 'ADDR004');
GO

-- 3. Accounts_Legacy Seed Data
INSERT INTO Accounts_Legacy (account_id, customer_id, account_type, balance, opened_date, status) VALUES ('A001', 'C001', 'SAVINGS', 15000.50, '2020-01-15', 'ACTIVE');
INSERT INTO Accounts_Legacy (account_id, customer_id, account_type, balance, opened_date, status) VALUES ('A002', 'C002', 'CHECKING', 4200.00, '2021-03-10', 'ACTIVE');
INSERT INTO Accounts_Legacy (account_id, customer_id, account_type, balance, opened_date, status) VALUES ('A003', 'C003', 'CURRENT', 8900.75, '2019-11-05', 'ACTIVE');
INSERT INTO Accounts_Legacy (account_id, customer_id, account_type, balance, opened_date, status) VALUES ('A005', 'C005', 'LOAN', 25000.00, '2022-05-20', 'ACTIVE');
INSERT INTO Accounts_Legacy (account_id, customer_id, account_type, balance, opened_date, status) VALUES ('A008', 'C008', 'SAVINGS', 35000.00, '2018-09-01', 'ACTIVE');
INSERT INTO Accounts_Legacy (account_id, customer_id, account_type, balance, opened_date, status) VALUES ('A009', 'C009', 'CHECKING', 1200.00, '2023-02-14', 'DORMANT');

-- DEFECT 5: Invalid negative balance on Savings Account (ACCOUNT_004 failure)
INSERT INTO Accounts_Legacy (account_id, customer_id, account_type, balance, opened_date, status) VALUES ('A004', 'C004', 'SAVINGS', -500.00, '2022-01-01', 'ACTIVE');

-- DEFECT 6: Invalid foreign key (References nonexistent customer C999 - ACCOUNT_002 failure)
INSERT INTO Accounts_Legacy (account_id, customer_id, account_type, balance, opened_date, status) VALUES ('A010', 'C999', 'SAVINGS', 5000.00, '2021-07-11', 'ACTIVE');
GO

-- 4. Transactions_Legacy Seed Data
INSERT INTO Transactions_Legacy (transaction_id, account_id, transaction_type, amount, transaction_date, description) VALUES ('TXN-1001', 'A001', 'DEPOSIT', 1000.00, '2026-08-01 10:00:00', ' Salary Deposit ');
INSERT INTO Transactions_Legacy (transaction_id, account_id, transaction_type, amount, transaction_date, description) VALUES ('TXN-1002', 'A001', 'WITHDRAWAL', 200.00, '2026-08-02 14:30:00', 'ATM Cash Withdrawal');
INSERT INTO Transactions_Legacy (transaction_id, account_id, transaction_type, amount, transaction_date, description) VALUES ('TXN-1003', 'A002', 'DEPOSIT', 500.00, '2026-08-03 09:15:00', 'Transfer in');
INSERT INTO Transactions_Legacy (transaction_id, account_id, transaction_type, amount, transaction_date, description) VALUES ('TXN-1004', 'A003', 'WITHDRAWAL', 150.75, '2026-08-04 16:45:00', 'POS Payment');
INSERT INTO Transactions_Legacy (transaction_id, account_id, transaction_type, amount, transaction_date, description) VALUES ('TXN-1006', 'A005', 'DEPOSIT', 1200.00, '2026-08-05 11:20:00', 'Loan repayment');
INSERT INTO Transactions_Legacy (transaction_id, account_id, transaction_type, amount, transaction_date, description) VALUES ('TXN-1007', 'A008', 'DEPOSIT', 5000.00, '2026-08-06 15:00:00', 'Wire transfer');

-- DEFECT 7: Duplicate transactions (TXN-1005 appears twice identically - TXN_005 failure)
INSERT INTO Transactions_Legacy (transaction_id, account_id, transaction_type, amount, transaction_date, description) VALUES ('TXN-1005', 'A001', 'DEPOSIT', 300.00, '2026-08-05 12:00:00', 'Duplicate Transfer');
INSERT INTO Transactions_Legacy (transaction_id, account_id, transaction_type, amount, transaction_date, description) VALUES ('TXN-1005', 'A001', 'DEPOSIT', 300.00, '2026-08-05 12:00:00', 'Duplicate Transfer');

-- DEFECT 8: Invalid foreign key (References nonexistent account A999999 - TXN_002 failure)
INSERT INTO Transactions_Legacy (transaction_id, account_id, transaction_type, amount, transaction_date, description) VALUES ('TXN-89231', 'A999999', 'TRANSFER', 250.00, '2026-08-07 13:10:00', 'Orphan Transaction');

-- DEFECT 9: Invalid transaction amount (Negative amount - TXN_003 failure)
INSERT INTO Transactions_Legacy (transaction_id, account_id, transaction_type, amount, transaction_date, description) VALUES ('TXN-1008', 'A002', 'DEPOSIT', -100.00, '2026-08-08 09:00:00', 'Negative deposit amount');
GO

-- 5. Loans_Legacy Seed Data
INSERT INTO Loans_Legacy (loan_id, account_id, loan_amount, interest_rate, term_months, start_date) VALUES ('LN-501', 'A005', 25000.00, 5.50, 60, '2022-05-20');
INSERT INTO Loans_Legacy (loan_id, account_id, loan_amount, interest_rate, term_months, start_date) VALUES ('LN-502', 'A003', 10000.00, 6.25, 36, '2023-01-15');
GO

-- 6. Beneficiaries_Legacy Seed Data
INSERT INTO Beneficiaries_Legacy (beneficiary_id, customer_id, beneficiary_name, account_number, routing_code) VALUES ('BEN-01', 'C001', 'Mary Smith', '987654321', 'ROUT001');
INSERT INTO Beneficiaries_Legacy (beneficiary_id, customer_id, beneficiary_name, account_number, routing_code) VALUES ('BEN-02', 'C002', 'Bob Cooper', '123456789', 'ROUT002');
GO
