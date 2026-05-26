-- =============================================================================
-- Mini Data Warehouse Schema
-- A compact star schema for demonstration and testing.
-- Dialect: DuckDB / ANSI SQL
-- =============================================================================

CREATE TABLE IF NOT EXISTS dim_product (
    product_sk   INTEGER PRIMARY KEY,
    product_id   VARCHAR NOT NULL,
    product_name VARCHAR NOT NULL,
    category     VARCHAR,
    unit_price   DECIMAL(10,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_customer (
    customer_sk  INTEGER PRIMARY KEY,
    customer_id  VARCHAR NOT NULL,
    full_name    VARCHAR NOT NULL,
    segment      VARCHAR DEFAULT 'Standard'
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_sk   INTEGER PRIMARY KEY,  -- YYYYMMDD
    full_date DATE NOT NULL,
    month     INTEGER NOT NULL,
    quarter   INTEGER NOT NULL,
    year      INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_sales (
    sales_sk     INTEGER PRIMARY KEY,
    customer_sk  INTEGER NOT NULL REFERENCES dim_customer(customer_sk),
    product_sk   INTEGER NOT NULL REFERENCES dim_product(product_sk),
    date_sk      INTEGER NOT NULL REFERENCES dim_date(date_sk),
    quantity     INTEGER NOT NULL,
    net_amount   DECIMAL(10,2) NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL
);
