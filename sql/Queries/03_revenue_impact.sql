-- ============================================================
-- SQL FILE 03: REVENUE IMPACT ANALYSIS
-- Customer Churn Project
-- ============================================================
-- This file answers the most important business question:
-- "How much money are we losing, and where is it coming from?"
-- Revenue numbers make executives pay attention.
-- ============================================================


-- QUERY 1: Total revenue lost to churn (headline number)
-- ============================================================
SELECT
    ROUND(SUM(CASE WHEN Churn = 'Yes' THEN MonthlyCharges ELSE 0 END), 0)
        AS monthly_revenue_lost,
    ROUND(SUM(CASE WHEN Churn = 'Yes' THEN MonthlyCharges ELSE 0 END) * 12, 0)
        AS annual_revenue_lost,
    ROUND(SUM(CASE WHEN Churn = 'No' THEN MonthlyCharges ELSE 0 END), 0)
        AS monthly_revenue_retained,
    ROUND(SUM(MonthlyCharges), 0)
        AS total_monthly_revenue,
    ROUND(
        SUM(CASE WHEN Churn = 'Yes' THEN MonthlyCharges ELSE 0 END) * 100.0
        / SUM(MonthlyCharges), 1
    ) AS pct_revenue_at_risk
FROM telco_churn_clean;


-- QUERY 2: Revenue lost by contract type
-- Which contract type costs us the most in lost revenue?
-- ============================================================
SELECT
    Contract,
    COUNT(CASE WHEN Churn = 'Yes' THEN 1 END) AS churned_customers,
    ROUND(SUM(CASE WHEN Churn = 'Yes' THEN MonthlyCharges ELSE 0 END), 0)
        AS monthly_revenue_lost,
    ROUND(AVG(CASE WHEN Churn = 'Yes' THEN MonthlyCharges END), 2)
        AS avg_charge_per_churned_customer
FROM telco_churn_clean
GROUP BY Contract
ORDER BY monthly_revenue_lost DESC;


-- QUERY 3: Revenue cohort analysis — value by tenure bucket
-- Are we losing high-value early customers or long-term customers?
-- Uses: CASE WHEN + SUM + GROUP BY
-- ============================================================
SELECT
    CASE
        WHEN tenure BETWEEN 0 AND 12  THEN '01: New (0-12 mo)'
        WHEN tenure BETWEEN 13 AND 24 THEN '02: Growing (13-24 mo)'
        WHEN tenure BETWEEN 25 AND 48 THEN '03: Established (25-48 mo)'
        ELSE '04: Loyal (49-72 mo)'
    END AS tenure_cohort,
    COUNT(*) AS total_customers,
    SUM(Churn_Binary) AS churned_customers,
    ROUND(AVG(Churn_Binary) * 100, 1) AS churn_rate_pct,
    ROUND(AVG(MonthlyCharges), 2) AS avg_monthly_charges,
    ROUND(SUM(CASE WHEN Churn = 'Yes' THEN MonthlyCharges ELSE 0 END), 0)
        AS monthly_revenue_lost,
    ROUND(SUM(CASE WHEN Churn = 'Yes' THEN MonthlyCharges * 12 ELSE 0 END), 0)
        AS annual_revenue_lost
FROM telco_churn_clean
GROUP BY 1
ORDER BY 1;


-- QUERY 4: Customer Lifetime Value (CLV) comparison — churned vs retained
-- CLV = average monthly charge × expected months remaining
-- This shows the TRUE cost of churn beyond just monthly charges
-- ============================================================
WITH clv_calc AS (
    SELECT
        Churn,
        tenure,
        MonthlyCharges,
        TotalCharges,
        -- Simple CLV: average monthly × average remaining tenure assumption
        -- Assuming average customer lifetime = 36 months if retained
        CASE
            WHEN Churn = 'No'
            THEN MonthlyCharges * (36 - tenure)  -- future value remaining
            ELSE 0
        END AS estimated_future_value,
        TotalCharges AS realized_value  -- what they already paid
    FROM telco_churn_clean
)
SELECT
    Churn,
    COUNT(*) AS customers,
    ROUND(AVG(tenure), 1) AS avg_tenure_months,
    ROUND(AVG(MonthlyCharges), 2) AS avg_monthly_charges,
    ROUND(AVG(realized_value), 2) AS avg_realized_value,
    ROUND(AVG(estimated_future_value), 2) AS avg_estimated_future_value
FROM clv_calc
GROUP BY Churn;


-- QUERY 5: Revenue recovery simulation
-- If we convert X% of month-to-month customers to annual contracts, 
-- how much churn revenue do we recover?
-- This is the "so what?" analysis that impresses business teams.
-- ============================================================
WITH month_to_month_churned AS (
    SELECT
        COUNT(*) AS m2m_churned_customers,
        ROUND(SUM(MonthlyCharges), 0) AS m2m_monthly_revenue_lost
    FROM telco_churn_clean
    WHERE Contract = 'Month-to-month' AND Churn = 'Yes'
),
annual_churn_rate AS (
    SELECT ROUND(AVG(Churn_Binary), 4) AS annual_contract_churn_rate
    FROM telco_churn_clean
    WHERE Contract = 'One year'
)
SELECT
    m.m2m_churned_customers,
    m.m2m_monthly_revenue_lost,
    a.annual_contract_churn_rate,
    -- If we converted these customers to annual contracts, how many would we save?
    ROUND(m.m2m_churned_customers * (0.42 - a.annual_contract_churn_rate)) AS customers_saved,
    -- Revenue saved per month
    ROUND(m.m2m_monthly_revenue_lost * (0.42 - a.annual_contract_churn_rate) / 0.42, 0)
        AS monthly_revenue_saved,
    ROUND(m.m2m_monthly_revenue_lost * (0.42 - a.annual_contract_churn_rate) / 0.42 * 12, 0)
        AS annual_revenue_saved
FROM month_to_month_churned m, annual_churn_rate a;
-- This query shows: converting month-to-month customers to annual saves ~$X per year


-- QUERY 6: Top 20 highest-value customers currently at risk
-- (Month-to-month contract, less than 24 months tenure)
-- This is your "retention call list" for the business
-- ============================================================
SELECT
    customerID,
    tenure,
    ROUND(MonthlyCharges, 2) AS monthly_charges,
    ROUND(TotalCharges, 2) AS total_paid_so_far,
    Contract,
    InternetService,
    PaymentMethod,
    -- Projected annual value if retained
    ROUND(MonthlyCharges * 12, 0) AS projected_annual_value
FROM telco_churn_clean
WHERE
    Churn = 'No'                          -- currently still a customer
    AND Contract = 'Month-to-month'       -- high churn risk
    AND tenure < 24                       -- early-stage customer
    AND MonthlyCharges > 70               -- high value
ORDER BY MonthlyCharges DESC
LIMIT 20;

-- ============================================================
-- SUMMARY OF KEY BUSINESS NUMBERS TO USE IN YOUR README:
-- ============================================================
-- Run this final summary query to get all headline numbers at once

SELECT
    'Total Customers' AS metric,
    CAST(COUNT(*) AS VARCHAR) AS value
FROM telco_churn_clean
UNION ALL
SELECT 'Churn Rate', ROUND(AVG(Churn_Binary)*100,1)||'%'
FROM telco_churn_clean
UNION ALL
SELECT 'Monthly Revenue Lost', '$'||ROUND(SUM(CASE WHEN Churn='Yes' THEN MonthlyCharges ELSE 0 END),0)
FROM telco_churn_clean
UNION ALL
SELECT 'Annual Revenue Lost', '$'||ROUND(SUM(CASE WHEN Churn='Yes' THEN MonthlyCharges ELSE 0 END)*12,0)
FROM telco_churn_clean
UNION ALL
SELECT 'Avg Charge Churned Customer', '$'||ROUND(AVG(CASE WHEN Churn='Yes' THEN MonthlyCharges END),2)
FROM telco_churn_clean
UNION ALL
SELECT 'Avg Charge Retained Customer', '$'||ROUND(AVG(CASE WHEN Churn='No' THEN MonthlyCharges END),2)
FROM telco_churn_clean;
