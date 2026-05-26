-- =============================================================================
-- Common Table Expression (CTE) Patterns
-- Dialect: ANSI SQL
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Modular query decomposition
-- Break a complex report into readable, testable stages.
-- -----------------------------------------------------------------------------
WITH
-- Stage 1: Aggregate sales at the customer level
customer_sales AS (
    SELECT
        f.customer_sk,
        COUNT(DISTINCT f.order_id)  AS order_count,
        SUM(f.net_amount)           AS lifetime_value,
        MIN(d.full_date)            AS first_order_date,
        MAX(d.full_date)            AS last_order_date
    FROM fact_sales AS f
    INNER JOIN dim_date AS d ON f.date_sk = d.date_sk
    GROUP BY f.customer_sk
),

-- Stage 2: Segment customers by value
customer_segments AS (
    SELECT
        cs.*,
        CASE
            WHEN lifetime_value >= 10000 THEN 'Platinum'
            WHEN lifetime_value >=  5000 THEN 'Gold'
            WHEN lifetime_value >=  1000 THEN 'Silver'
            ELSE 'Bronze'
        END AS value_tier,
        last_order_date - first_order_date AS customer_tenure_days
    FROM customer_sales AS cs
),

-- Stage 3: Enrich with dimension attributes
enriched AS (
    SELECT
        c.customer_id,
        c.first_name,
        c.last_name,
        c.customer_segment,
        seg.value_tier,
        seg.order_count,
        seg.lifetime_value,
        seg.customer_tenure_days,
        seg.first_order_date,
        seg.last_order_date
    FROM customer_segments AS seg
    INNER JOIN dim_customer AS c
        ON seg.customer_sk = c.customer_sk
        AND c.is_current = TRUE
)

-- Final output
SELECT *
FROM enriched
ORDER BY lifetime_value DESC;


-- -----------------------------------------------------------------------------
-- 2. Recursive CTE: Generate a date spine
-- Useful when dim_date is missing or you need an ad-hoc date range.
-- -----------------------------------------------------------------------------
WITH RECURSIVE date_spine AS (
    -- Anchor: starting date
    SELECT DATE '2024-01-01' AS spine_date

    UNION ALL

    -- Recursive step: add one day
    SELECT spine_date + INTERVAL '1 day'
    FROM date_spine
    WHERE spine_date < DATE '2024-12-31'
)
SELECT
    spine_date,
    EXTRACT(DOW FROM spine_date)   AS day_of_week,
    EXTRACT(MONTH FROM spine_date) AS month_number,
    EXTRACT(QUARTER FROM spine_date) AS quarter
FROM date_spine
ORDER BY spine_date;


-- -----------------------------------------------------------------------------
-- 3. Recursive CTE: Flatten an organizational hierarchy
-- Traverses a parent-child employee table to compute reporting depth.
-- -----------------------------------------------------------------------------
WITH RECURSIVE org_tree AS (
    -- Anchor: top-level managers (no manager_id)
    SELECT
        employee_id,
        employee_name,
        manager_id,
        1 AS depth,
        employee_name AS reporting_chain
    FROM employees
    WHERE manager_id IS NULL

    UNION ALL

    -- Recursive step: employees who report to someone already in the tree
    SELECT
        e.employee_id,
        e.employee_name,
        e.manager_id,
        t.depth + 1,
        t.reporting_chain || ' > ' || e.employee_name
    FROM employees AS e
    INNER JOIN org_tree AS t ON e.manager_id = t.employee_id
)
SELECT employee_id, employee_name, depth, reporting_chain
FROM org_tree
ORDER BY depth, employee_name;
