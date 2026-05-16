-- ============================================================
-- SQL FILE 01: DATA EXPLORATION
-- Customer Churn Project
-- ============================================================
-- HOW TO USE:
-- 1. Install PostgreSQL (free): https://www.postgresql.org/download/
-- 2. Install pgAdmin (free GUI): https://www.pgadmin.org/download/
-- 3. Create a new database called "churn_db"
-- 4. Import the CSV: right-click table → Import/Export → select telco_churn.csv
-- 5. Run each query below one at a time (select it and press F5)
-- ============================================================


-- STEP 1: Create the table first (run this BEFORE importing CSV)
-- ============================================================
CREATE TABLE IF NOT EXISTS telco_churn (
    customerID        VARCHAR(20) PRIMARY KEY,
    gender            VARCHAR(10),
    SeniorCitizen     INTEGER,
    Partner           VARCHAR(5),
    Dependents        VARCHAR(5),
    tenure            INTEGER,
    PhoneService      VARCHAR(5),
    MultipleLines     VARCHAR(25),
    InternetService   VARCHAR(25),
    OnlineSecurity    VARCHAR(25),
    OnlineBackup      VARCHAR(25),
    DeviceProtection  VARCHAR(25),
    TechSupport       VARCHAR(25),
    StreamingTV       VARCHAR(25),
    StreamingMovies   VARCHAR(25),
    Contract          VARCHAR(25),
    PaperlessBilling  VARCHAR(5),
    PaymentMethod     VARCHAR(35),
    MonthlyCharges    NUMERIC(8,2),
    TotalCharges      VARCHAR(15),  -- stored as text in original CSV
    Churn             VARCHAR(5)
);


-- STEP 2: Check the data loaded correctly
-- ============================================================
-- How many rows?
SELECT COUNT(*) AS total_customers FROM telco_churn;

-- See first 10 rows
SELECT * FROM telco_churn LIMIT 10;

-- Check column data types
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'telco_churn'
ORDER BY ordinal_position;


-- STEP 3: Check for data quality issues
-- ============================================================
-- Find NULL or empty values in each key column
SELECT
    COUNT(*) AS total_rows,
    COUNT(CASE WHEN customerID IS NULL THEN 1 END) AS null_customer_ids,
    COUNT(CASE WHEN tenure IS NULL THEN 1 END) AS null_tenure,
    COUNT(CASE WHEN MonthlyCharges IS NULL THEN 1 END) AS null_monthly_charges,
    COUNT(CASE WHEN TotalCharges = '' OR TotalCharges = ' ' THEN 1 END) AS empty_total_charges,
    COUNT(CASE WHEN Churn IS NULL THEN 1 END) AS null_churn
FROM telco_churn;
-- Note: TotalCharges has blank spaces instead of NULLs — this is the data quality issue!


-- STEP 4: Fix TotalCharges data type issue
-- ============================================================
-- Create a clean view with TotalCharges as proper number
CREATE OR REPLACE VIEW telco_churn_clean AS
SELECT
    customerID,
    gender,
    SeniorCitizen,
    Partner,
    Dependents,
    tenure,
    PhoneService,
    MultipleLines,
    InternetService,
    OnlineSecurity,
    OnlineBackup,
    DeviceProtection,
    TechSupport,
    StreamingTV,
    StreamingMovies,
    Contract,
    PaperlessBilling,
    PaymentMethod,
    MonthlyCharges,
    CASE
        WHEN TRIM(TotalCharges) = '' THEN 0
        ELSE CAST(TRIM(TotalCharges) AS NUMERIC)
    END AS TotalCharges,
    Churn,
    CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END AS Churn_Binary
FROM telco_churn;

-- Verify the fix
SELECT COUNT(*) FROM telco_churn_clean WHERE TotalCharges = 0;
-- Should return 11 rows (new customers with 0 tenure)


-- STEP 5: Basic summary statistics
-- ============================================================
SELECT
    ROUND(AVG(tenure), 1) AS avg_tenure_months,
    ROUND(MIN(tenure), 1) AS min_tenure,
    ROUND(MAX(tenure), 1) AS max_tenure,
    ROUND(AVG(MonthlyCharges), 2) AS avg_monthly_charge,
    ROUND(MIN(MonthlyCharges), 2) AS min_monthly_charge,
    ROUND(MAX(MonthlyCharges), 2) AS max_monthly_charge,
    ROUND(AVG(TotalCharges), 2) AS avg_total_charges
FROM telco_churn_clean;
