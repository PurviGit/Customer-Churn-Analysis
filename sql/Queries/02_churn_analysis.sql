-- ============================================================
-- SQL FILE 02: CHURN ANALYSIS QUERIES
-- Customer Churn Project
-- ============================================================
-- These queries are the HEART of the SQL part of your project.
-- Each query answers a specific business question.
-- Copy these findings into your README and dashboard.
-- ============================================================


-- QUERY 1: Overall churn rate
-- Business question: What is our churn problem at a glance?
-- ============================================================
SELECT
    Churn,
    COUNT(*) AS customer_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS percentage
FROM telco_churn_clean
GROUP BY Churn
ORDER BY Churn DESC;
-- EXPECTED RESULT: ~26.5% churned, ~73.5% retained


-- QUERY 2: Churn rate by contract type (MOST IMPORTANT QUERY)
-- Business question: Which contract type has the highest churn?
-- Uses: GROUP BY, ROUND, ORDER BY
-- ============================================================
SELECT
    Contract,
    COUNT(*) AS total_customers,
    SUM(Churn_Binary) AS churned_customers,
    ROUND(AVG(Churn_Binary) * 100, 1) AS churn_rate_pct,
    ROUND(AVG(MonthlyCharges), 2) AS avg_monthly_charges
FROM telco_churn_clean
GROUP BY Contract
ORDER BY churn_rate_pct DESC;
-- EXPECTED: Month-to-month ~42%, One year ~11%, Two year ~3%
-- BUSINESS INSIGHT: Month-to-month customers churn 14x more than two-year subscribers!


-- QUERY 3: Churn by tenure group using CASE WHEN
-- Business question: Do new customers churn more than established ones?
-- Uses: CASE WHEN (creates categories), GROUP BY, ORDER BY
-- ============================================================
SELECT
    CASE
        WHEN tenure BETWEEN 0 AND 12 THEN '0-12 months (New)'
        WHEN tenure BETWEEN 13 AND 24 THEN '13-24 months (Growing)'
        WHEN tenure BETWEEN 25 AND 48 THEN '25-48 months (Established)'
        WHEN tenure BETWEEN 49 AND 72 THEN '49-72 months (Loyal)'
    END AS tenure_group,
    COUNT(*) AS total_customers,
    SUM(Churn_Binary) AS churned_count,
    ROUND(AVG(Churn_Binary) * 100, 1) AS churn_rate_pct,
    ROUND(AVG(MonthlyCharges), 2) AS avg_monthly_charges
FROM telco_churn_clean
GROUP BY 1  -- group by the CASE WHEN column (column 1)
ORDER BY churn_rate_pct DESC;


-- QUERY 4: Churn by internet service type
-- Business question: Are premium internet customers churning more?
-- ============================================================
SELECT
    InternetService,
    COUNT(*) AS total_customers,
    SUM(Churn_Binary) AS churned_customers,
    ROUND(AVG(Churn_Binary) * 100, 1) AS churn_rate_pct,
    ROUND(AVG(MonthlyCharges), 2) AS avg_monthly_charges
FROM telco_churn_clean
GROUP BY InternetService
ORDER BY churn_rate_pct DESC;
-- BUSINESS INSIGHT: Fiber optic customers pay MORE but churn MORE — service quality issue?


-- QUERY 5: Multi-dimensional churn analysis (Contract + Internet)
-- Business question: Which COMBINATION of factors creates highest churn?
-- Uses: Multi-column GROUP BY
-- ============================================================
SELECT
    Contract,
    InternetService,
    COUNT(*) AS total_customers,
    SUM(Churn_Binary) AS churned_customers,
    ROUND(AVG(Churn_Binary) * 100, 1) AS churn_rate_pct
FROM telco_churn_clean
GROUP BY Contract, InternetService
HAVING COUNT(*) > 50  -- only show groups with 50+ customers (statistically meaningful)
ORDER BY churn_rate_pct DESC;


-- QUERY 6: Senior citizen churn analysis
-- Business question: Are senior customers churning at different rates?
-- Uses: CASE WHEN to label 0/1 values
-- ============================================================
SELECT
    CASE WHEN SeniorCitizen = 1 THEN 'Senior Citizen' ELSE 'Non-Senior' END AS customer_segment,
    COUNT(*) AS total_customers,
    SUM(Churn_Binary) AS churned_customers,
    ROUND(AVG(Churn_Binary) * 100, 1) AS churn_rate_pct,
    ROUND(AVG(MonthlyCharges), 2) AS avg_monthly_charges
FROM telco_churn_clean
GROUP BY SeniorCitizen
ORDER BY churn_rate_pct DESC;


-- QUERY 7: Payment method analysis
-- Business question: Do customers on electronic check churn more?
-- (Often a sign of disengaged customers)
-- ============================================================
SELECT
    PaymentMethod,
    COUNT(*) AS total_customers,
    SUM(Churn_Binary) AS churned_customers,
    ROUND(AVG(Churn_Binary) * 100, 1) AS churn_rate_pct
FROM telco_churn_clean
GROUP BY PaymentMethod
ORDER BY churn_rate_pct DESC;


-- QUERY 8: Churn rate by number of services (using subquery)
-- Business question: Do customers with more services churn less?
-- Uses: SUBQUERY — a query inside a query
-- ============================================================
SELECT
    NumServices,
    COUNT(*) AS total_customers,
    SUM(Churn_Binary) AS churned_customers,
    ROUND(AVG(Churn_Binary) * 100, 1) AS churn_rate_pct
FROM (
    -- Inner query: calculate number of services per customer
    SELECT
        customerID,
        Churn_Binary,
        (
            CASE WHEN PhoneService = 'Yes' THEN 1 ELSE 0 END +
            CASE WHEN OnlineSecurity = 'Yes' THEN 1 ELSE 0 END +
            CASE WHEN OnlineBackup = 'Yes' THEN 1 ELSE 0 END +
            CASE WHEN DeviceProtection = 'Yes' THEN 1 ELSE 0 END +
            CASE WHEN TechSupport = 'Yes' THEN 1 ELSE 0 END +
            CASE WHEN StreamingTV = 'Yes' THEN 1 ELSE 0 END +
            CASE WHEN StreamingMovies = 'Yes' THEN 1 ELSE 0 END
        ) AS NumServices
    FROM telco_churn_clean
) AS services_count
GROUP BY NumServices
ORDER BY NumServices;
-- EXPECTED: Customers with 0 services churn ~20%, customers with 7 services churn ~5%


-- QUERY 9: Window functions — running churn rate by month
-- Business question: How does churn rate change as tenure increases?
-- Uses: WINDOW FUNCTION (AVG OVER) — advanced SQL skill!
-- ============================================================
SELECT
    tenure,
    COUNT(*) AS customers_at_this_tenure,
    SUM(Churn_Binary) AS churned_at_this_tenure,
    ROUND(AVG(Churn_Binary) * 100, 1) AS monthly_churn_rate,
    ROUND(AVG(AVG(Churn_Binary)) OVER (
        ORDER BY tenure ROWS BETWEEN 2 PRECEDING AND 2 FOLLOWING
    ) * 100, 1) AS rolling_3month_avg_churn  -- smoothed trend line
FROM telco_churn_clean
GROUP BY tenure
ORDER BY tenure;
-- WINDOW FUNCTION EXPLANATION:
-- OVER() = "apply this calculation across a window of rows"
-- ROWS BETWEEN 2 PRECEDING AND 2 FOLLOWING = use 5 rows centered on current row
-- This smooths out month-to-month noise and shows the real trend


-- QUERY 10: CTE (Common Table Expression) — Churn risk ranking
-- Business question: How do we rank customers by churn risk for campaigns?
-- Uses: CTE (WITH clause) — the most important SQL skill for analysts!
-- ============================================================
WITH customer_risk AS (
    -- Step 1: Score each customer's churn risk based on known risk factors
    SELECT
        customerID,
        tenure,
        MonthlyCharges,
        Contract,
        InternetService,
        Churn,
        -- Risk score: higher = more likely to churn
        -- Based on findings from our previous queries
        (
            CASE WHEN Contract = 'Month-to-month' THEN 40 ELSE 0 END +
            CASE WHEN tenure <= 12 THEN 30 ELSE 0 END +
            CASE WHEN tenure BETWEEN 13 AND 24 THEN 15 ELSE 0 END +
            CASE WHEN InternetService = 'Fiber optic' THEN 20 ELSE 0 END +
            CASE WHEN SeniorCitizen = 1 THEN 10 ELSE 0 END
        ) AS risk_score
    FROM telco_churn_clean
),
risk_ranked AS (
    -- Step 2: Rank customers by risk score and add revenue info
    SELECT
        customerID,
        tenure,
        MonthlyCharges,
        Contract,
        InternetService,
        Churn,
        risk_score,
        RANK() OVER (ORDER BY risk_score DESC, MonthlyCharges DESC) AS risk_rank,
        CASE
            WHEN risk_score >= 70 THEN 'HIGH RISK'
            WHEN risk_score >= 40 THEN 'MEDIUM RISK'
            ELSE 'LOW RISK'
        END AS risk_category
    FROM customer_risk
)
-- Step 3: Show high-risk customers sorted by monthly value (target highest value first)
SELECT
    risk_rank,
    customerID,
    tenure,
    ROUND(MonthlyCharges, 2) AS monthly_charges,
    Contract,
    InternetService,
    risk_score,
    risk_category,
    Churn AS actual_churn  -- to verify our risk scoring accuracy
FROM risk_ranked
WHERE risk_category = 'HIGH RISK'
ORDER BY MonthlyCharges DESC
LIMIT 20;

-- ============================================================
-- 🎯 WHAT TO WRITE ON YOUR RESUME FOR SQL SECTION:
-- "Wrote 10 SQL queries using CTEs, window functions, subqueries,
-- and CASE WHEN logic to analyze churn patterns across 7,000+
-- telecom customers; identified month-to-month contract customers
-- as 14x more likely to churn than two-year subscribers."
-- ============================================================
