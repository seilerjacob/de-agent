-- =============================================================================
-- Dimensional Model: E-Commerce Star Schema
-- Dialect: ANSI SQL (with notes for Snowflake/BigQuery where applicable)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Dimension: dim_customer (SCD Type 2)
-- Tracks historical changes to customer attributes.
-- -----------------------------------------------------------------------------
CREATE TABLE dim_customer (
    customer_sk        INT            NOT NULL,  -- surrogate key
    customer_id        VARCHAR(50)    NOT NULL,  -- natural/business key
    first_name         VARCHAR(100)   NOT NULL,
    last_name          VARCHAR(100)   NOT NULL,
    email              VARCHAR(255),
    customer_segment   VARCHAR(50)    DEFAULT 'Standard',
    city               VARCHAR(100),
    state              VARCHAR(50),
    country            VARCHAR(50),
    -- SCD Type 2 metadata
    effective_date     DATE           NOT NULL,
    expiration_date    DATE,                       -- NULL = current record
    is_current         BOOLEAN        NOT NULL DEFAULT TRUE,
    -- Audit columns
    created_at         TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    loaded_at          TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (customer_sk)
);

-- -----------------------------------------------------------------------------
-- Dimension: dim_product
-- Standard (Type 1) dimension for product catalog.
-- -----------------------------------------------------------------------------
CREATE TABLE dim_product (
    product_sk         INT            NOT NULL,
    product_id         VARCHAR(50)    NOT NULL,
    product_name       VARCHAR(255)   NOT NULL,
    category           VARCHAR(100),
    subcategory        VARCHAR(100),
    brand              VARCHAR(100),
    unit_price         DECIMAL(12,2)  NOT NULL,
    is_active          BOOLEAN        NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    loaded_at          TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (product_sk)
);

-- -----------------------------------------------------------------------------
-- Dimension: dim_date
-- Pre-populated calendar dimension.
-- -----------------------------------------------------------------------------
CREATE TABLE dim_date (
    date_sk            INT            NOT NULL,  -- YYYYMMDD integer key
    full_date          DATE           NOT NULL,
    day_of_week        SMALLINT       NOT NULL,  -- 1=Monday .. 7=Sunday
    day_name           VARCHAR(10)    NOT NULL,
    month_number       SMALLINT       NOT NULL,
    month_name         VARCHAR(10)    NOT NULL,
    quarter            SMALLINT       NOT NULL,
    year               INT            NOT NULL,
    is_weekend         BOOLEAN        NOT NULL,
    is_holiday         BOOLEAN        NOT NULL DEFAULT FALSE,
    fiscal_quarter     SMALLINT,
    fiscal_year        INT,
    PRIMARY KEY (date_sk)
);

-- -----------------------------------------------------------------------------
-- Dimension: dim_store
-- Retail location dimension.
-- -----------------------------------------------------------------------------
CREATE TABLE dim_store (
    store_sk           INT            NOT NULL,
    store_id           VARCHAR(50)    NOT NULL,
    store_name         VARCHAR(255)   NOT NULL,
    store_type         VARCHAR(50),               -- e.g., 'Retail', 'Online'
    city               VARCHAR(100),
    state              VARCHAR(50),
    country            VARCHAR(50),
    region             VARCHAR(50),
    open_date          DATE,
    is_active          BOOLEAN        NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    loaded_at          TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (store_sk)
);

-- -----------------------------------------------------------------------------
-- Fact: fact_sales
-- Grain: one row per order line item.
-- -----------------------------------------------------------------------------
CREATE TABLE fact_sales (
    sales_sk           BIGINT         NOT NULL,
    order_id           VARCHAR(50)    NOT NULL,
    line_item_number   SMALLINT       NOT NULL,
    -- Foreign keys to dimensions
    customer_sk        INT            NOT NULL,
    product_sk         INT            NOT NULL,
    date_sk            INT            NOT NULL,
    store_sk           INT            NOT NULL,
    -- Measures
    quantity           INT            NOT NULL,
    unit_price         DECIMAL(12,2)  NOT NULL,
    discount_amount    DECIMAL(12,2)  NOT NULL DEFAULT 0,
    net_amount         DECIMAL(12,2)  NOT NULL,  -- (quantity * unit_price) - discount
    tax_amount         DECIMAL(12,2)  NOT NULL DEFAULT 0,
    total_amount       DECIMAL(12,2)  NOT NULL,  -- net_amount + tax_amount
    -- Audit
    loaded_at          TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (sales_sk),
    FOREIGN KEY (customer_sk) REFERENCES dim_customer(customer_sk),
    FOREIGN KEY (product_sk)  REFERENCES dim_product(product_sk),
    FOREIGN KEY (date_sk)     REFERENCES dim_date(date_sk),
    FOREIGN KEY (store_sk)    REFERENCES dim_store(store_sk)
);
