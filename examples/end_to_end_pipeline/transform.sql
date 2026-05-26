-- =============================================================================
-- Transform — SQL logic executed via DuckDB against extracted CSV data.
-- Called from load.py using duckdb.sql().
-- =============================================================================

-- Step 1: Read the raw CSV and apply cleaning + derived columns
CREATE OR REPLACE TABLE staged_sales AS
SELECT
    order_id,
    line_item_number,
    CAST(order_date AS DATE)       AS order_date,
    TRIM(LOWER(customer_id))       AS customer_id,
    TRIM(LOWER(store_id))          AS store_id,
    TRIM(LOWER(product_id))        AS product_id,
    TRIM(LOWER(product_name))      AS product_name,
    TRIM(LOWER(category))          AS category,
    quantity,
    unit_price,
    COALESCE(discount_amount, 0)   AS discount_amount,
    COALESCE(tax_amount, 0)        AS tax_amount,
    -- Derived measures
    (quantity * unit_price) - COALESCE(discount_amount, 0)                          AS net_amount,
    (quantity * unit_price) - COALESCE(discount_amount, 0) + COALESCE(tax_amount, 0) AS total_amount,
    CURRENT_TIMESTAMP              AS loaded_at
FROM raw_sales;


-- Step 2: Summary view for quick validation
CREATE OR REPLACE VIEW sales_summary AS
SELECT
    category,
    COUNT(DISTINCT order_id)  AS order_count,
    SUM(quantity)             AS total_units,
    ROUND(SUM(net_amount), 2) AS total_net,
    ROUND(SUM(total_amount), 2) AS total_gross
FROM staged_sales
GROUP BY category
ORDER BY total_gross DESC;
