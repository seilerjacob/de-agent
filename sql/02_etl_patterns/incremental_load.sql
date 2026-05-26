-- =============================================================================
-- Incremental Load Pattern
-- Uses a high-water mark to detect new or changed rows and MERGE to upsert.
-- Dialect: ANSI SQL / Snowflake-compatible
-- =============================================================================

-- Step 1: Identify the current high-water mark (last successful load timestamp)
-- In production this would come from a control table or orchestration metadata.
WITH high_water AS (
    SELECT COALESCE(MAX(loaded_at), '1900-01-01'::TIMESTAMP) AS hwm
    FROM target_schema.fact_sales
),

-- Step 2: Extract only rows modified since the high-water mark
new_rows AS (
    SELECT
        s.order_id,
        s.line_item_number,
        s.customer_id,
        s.product_id,
        s.order_date,
        s.store_id,
        s.quantity,
        s.unit_price,
        s.discount_amount,
        s.tax_amount,
        s.updated_at
    FROM source_schema.raw_sales AS s
    CROSS JOIN high_water AS hw
    WHERE s.updated_at > hw.hwm
)

-- Step 3: Merge into the target table
MERGE INTO target_schema.fact_sales AS tgt
USING new_rows AS src
    ON  tgt.order_id         = src.order_id
    AND tgt.line_item_number = src.line_item_number

-- Update existing rows if source has changed
WHEN MATCHED AND src.updated_at > tgt.updated_at THEN
    UPDATE SET
        tgt.quantity        = src.quantity,
        tgt.unit_price      = src.unit_price,
        tgt.discount_amount = src.discount_amount,
        tgt.net_amount      = (src.quantity * src.unit_price) - src.discount_amount,
        tgt.tax_amount      = src.tax_amount,
        tgt.total_amount    = ((src.quantity * src.unit_price) - src.discount_amount) + src.tax_amount,
        tgt.loaded_at       = CURRENT_TIMESTAMP

-- Insert new rows
WHEN NOT MATCHED THEN
    INSERT (
        order_id, line_item_number, customer_sk, product_sk, date_sk, store_sk,
        quantity, unit_price, discount_amount, net_amount, tax_amount, total_amount,
        loaded_at
    )
    VALUES (
        src.order_id,
        src.line_item_number,
        -- In production, look up surrogate keys from dimension tables
        (SELECT customer_sk FROM dim_customer WHERE customer_id = src.customer_id AND is_current = TRUE),
        (SELECT product_sk  FROM dim_product  WHERE product_id  = src.product_id),
        (SELECT date_sk     FROM dim_date     WHERE full_date   = src.order_date),
        (SELECT store_sk    FROM dim_store    WHERE store_id    = src.store_id),
        src.quantity,
        src.unit_price,
        src.discount_amount,
        (src.quantity * src.unit_price) - src.discount_amount,
        src.tax_amount,
        ((src.quantity * src.unit_price) - src.discount_amount) + src.tax_amount,
        CURRENT_TIMESTAMP
    );
