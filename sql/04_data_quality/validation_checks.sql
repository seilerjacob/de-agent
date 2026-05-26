-- =============================================================================
-- Data Quality Validation Checks
-- Run after each load to catch issues early.
-- Dialect: ANSI SQL
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Null checks on required columns
-- Returns rows where any NOT-NULL-expected column is actually NULL.
-- -----------------------------------------------------------------------------
SELECT 'fact_sales.order_id'   AS check_name, COUNT(*) AS failing_rows
FROM fact_sales WHERE order_id IS NULL
UNION ALL
SELECT 'fact_sales.customer_sk', COUNT(*)
FROM fact_sales WHERE customer_sk IS NULL
UNION ALL
SELECT 'fact_sales.product_sk', COUNT(*)
FROM fact_sales WHERE product_sk IS NULL
UNION ALL
SELECT 'fact_sales.quantity', COUNT(*)
FROM fact_sales WHERE quantity IS NULL
UNION ALL
SELECT 'fact_sales.net_amount', COUNT(*)
FROM fact_sales WHERE net_amount IS NULL;


-- -----------------------------------------------------------------------------
-- 2. Uniqueness check
-- Ensures no duplicate order line items exist.
-- -----------------------------------------------------------------------------
SELECT
    'fact_sales unique(order_id, line_item_number)' AS check_name,
    COUNT(*) AS duplicate_count
FROM (
    SELECT order_id, line_item_number
    FROM fact_sales
    GROUP BY order_id, line_item_number
    HAVING COUNT(*) > 1
) AS dupes;


-- -----------------------------------------------------------------------------
-- 3. Referential integrity
-- Finds fact rows pointing to non-existent dimension keys.
-- -----------------------------------------------------------------------------
SELECT 'fact_sales → dim_customer' AS check_name, COUNT(*) AS orphan_rows
FROM fact_sales AS f
LEFT JOIN dim_customer AS c ON f.customer_sk = c.customer_sk
WHERE c.customer_sk IS NULL

UNION ALL

SELECT 'fact_sales → dim_product', COUNT(*)
FROM fact_sales AS f
LEFT JOIN dim_product AS p ON f.product_sk = p.product_sk
WHERE p.product_sk IS NULL

UNION ALL

SELECT 'fact_sales → dim_date', COUNT(*)
FROM fact_sales AS f
LEFT JOIN dim_date AS d ON f.date_sk = d.date_sk
WHERE d.date_sk IS NULL

UNION ALL

SELECT 'fact_sales → dim_store', COUNT(*)
FROM fact_sales AS f
LEFT JOIN dim_store AS s ON f.store_sk = s.store_sk
WHERE s.store_sk IS NULL;


-- -----------------------------------------------------------------------------
-- 4. Range and format validation
-- Checks that numeric measures and dates fall within acceptable bounds.
-- -----------------------------------------------------------------------------
SELECT 'quantity <= 0'      AS check_name, COUNT(*) AS failing_rows
FROM fact_sales WHERE quantity <= 0

UNION ALL
SELECT 'net_amount < 0',    COUNT(*)
FROM fact_sales WHERE net_amount < 0

UNION ALL
SELECT 'discount > net+discount', COUNT(*)
FROM fact_sales WHERE discount_amount > (net_amount + discount_amount)

UNION ALL
SELECT 'future order date', COUNT(*)
FROM fact_sales AS f
INNER JOIN dim_date AS d ON f.date_sk = d.date_sk
WHERE d.full_date > CURRENT_DATE;


-- -----------------------------------------------------------------------------
-- 5. Row count anomaly detection
-- Compares today's load count against the 7-day rolling average.
-- Flags if today's count deviates by more than 50%.
-- -----------------------------------------------------------------------------
WITH daily_counts AS (
    SELECT
        d.full_date,
        COUNT(*) AS row_count
    FROM fact_sales AS f
    INNER JOIN dim_date AS d ON f.date_sk = d.date_sk
    WHERE d.full_date BETWEEN CURRENT_DATE - INTERVAL '7 days' AND CURRENT_DATE
    GROUP BY d.full_date
),
stats AS (
    SELECT
        MAX(CASE WHEN full_date = CURRENT_DATE THEN row_count END) AS today_count,
        AVG(row_count) AS avg_7d
    FROM daily_counts
)
SELECT
    'row_count_anomaly' AS check_name,
    today_count,
    ROUND(avg_7d, 0) AS avg_7d,
    ROUND(ABS(today_count - avg_7d) / NULLIF(avg_7d, 0) * 100, 1) AS pct_deviation,
    CASE
        WHEN ABS(today_count - avg_7d) / NULLIF(avg_7d, 0) > 0.50 THEN 'FAIL'
        ELSE 'PASS'
    END AS status
FROM stats;
