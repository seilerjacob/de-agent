-- =============================================================================
-- Window Function Patterns for Data Engineering
-- Dialect: ANSI SQL
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Ranking: Top N products per category by revenue
-- -----------------------------------------------------------------------------
WITH product_revenue AS (
    SELECT
        p.category,
        p.product_name,
        SUM(f.net_amount) AS total_revenue
    FROM fact_sales  AS f
    INNER JOIN dim_product AS p ON f.product_sk = p.product_sk
    GROUP BY p.category, p.product_name
),
ranked AS (
    SELECT
        category,
        product_name,
        total_revenue,
        ROW_NUMBER() OVER (
            PARTITION BY category
            ORDER BY total_revenue DESC
        ) AS revenue_rank
    FROM product_revenue
)
SELECT category, product_name, total_revenue, revenue_rank
FROM ranked
WHERE revenue_rank <= 5
ORDER BY category, revenue_rank;


-- -----------------------------------------------------------------------------
-- 2. Running total: Cumulative daily sales
-- -----------------------------------------------------------------------------
SELECT
    d.full_date,
    SUM(f.total_amount)  AS daily_sales,
    SUM(SUM(f.total_amount)) OVER (
        ORDER BY d.full_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_sales
FROM fact_sales AS f
INNER JOIN dim_date AS d ON f.date_sk = d.date_sk
WHERE d.year = 2025
GROUP BY d.full_date
ORDER BY d.full_date;


-- -----------------------------------------------------------------------------
-- 3. Moving average: 7-day rolling average of daily sales
-- -----------------------------------------------------------------------------
WITH daily AS (
    SELECT
        d.full_date,
        SUM(f.total_amount) AS daily_sales
    FROM fact_sales AS f
    INNER JOIN dim_date AS d ON f.date_sk = d.date_sk
    GROUP BY d.full_date
)
SELECT
    full_date,
    daily_sales,
    AVG(daily_sales) OVER (
        ORDER BY full_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS rolling_7d_avg
FROM daily
ORDER BY full_date;


-- -----------------------------------------------------------------------------
-- 4. Lead/Lag: Days between consecutive customer orders
-- -----------------------------------------------------------------------------
WITH customer_orders AS (
    SELECT
        c.customer_id,
        d.full_date AS order_date,
        LAG(d.full_date) OVER (
            PARTITION BY c.customer_id
            ORDER BY d.full_date
        ) AS previous_order_date
    FROM fact_sales  AS f
    INNER JOIN dim_customer AS c ON f.customer_sk = c.customer_sk AND c.is_current = TRUE
    INNER JOIN dim_date     AS d ON f.date_sk     = d.date_sk
    GROUP BY c.customer_id, d.full_date
)
SELECT
    customer_id,
    order_date,
    previous_order_date,
    order_date - previous_order_date AS days_between_orders
FROM customer_orders
WHERE previous_order_date IS NOT NULL
ORDER BY customer_id, order_date;


-- -----------------------------------------------------------------------------
-- 5. Percent of total: Each store's contribution to total revenue
-- -----------------------------------------------------------------------------
SELECT
    s.store_name,
    SUM(f.net_amount) AS store_revenue,
    SUM(f.net_amount) * 100.0 / SUM(SUM(f.net_amount)) OVER () AS pct_of_total
FROM fact_sales AS f
INNER JOIN dim_store AS s ON f.store_sk = s.store_sk
GROUP BY s.store_name
ORDER BY store_revenue DESC;
