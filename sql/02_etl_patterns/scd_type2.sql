-- =============================================================================
-- Slowly Changing Dimension (SCD) Type 2 — MERGE Pattern
-- Expires old records and inserts new versions when attributes change.
-- Dialect: ANSI SQL / Snowflake-compatible
-- =============================================================================

-- Step 1: Stage incoming customer data with a hash of tracked attributes
-- so we can efficiently detect changes.
WITH staged AS (
    SELECT
        customer_id,
        first_name,
        last_name,
        email,
        customer_segment,
        city,
        state,
        country,
        -- Hash the trackable attributes to detect changes
        MD5(
            COALESCE(first_name, '')  || '|' ||
            COALESCE(last_name, '')   || '|' ||
            COALESCE(email, '')       || '|' ||
            COALESCE(customer_segment, '') || '|' ||
            COALESCE(city, '')        || '|' ||
            COALESCE(state, '')       || '|' ||
            COALESCE(country, '')
        ) AS attribute_hash
    FROM source_schema.raw_customers
),

-- Step 2: Compare against current dimension records
current_dim AS (
    SELECT
        customer_sk,
        customer_id,
        MD5(
            COALESCE(first_name, '')  || '|' ||
            COALESCE(last_name, '')   || '|' ||
            COALESCE(email, '')       || '|' ||
            COALESCE(customer_segment, '') || '|' ||
            COALESCE(city, '')        || '|' ||
            COALESCE(state, '')       || '|' ||
            COALESCE(country, '')
        ) AS attribute_hash
    FROM dim_customer
    WHERE is_current = TRUE
)

-- Step 3: Apply the SCD Type 2 logic
-- 3a: Expire changed records (set expiration_date and is_current = FALSE)
MERGE INTO dim_customer AS tgt
USING (
    SELECT s.*, c.customer_sk
    FROM staged AS s
    INNER JOIN current_dim AS c
        ON s.customer_id = c.customer_id
    WHERE s.attribute_hash <> c.attribute_hash   -- attributes changed
) AS changed
    ON tgt.customer_sk = changed.customer_sk

WHEN MATCHED THEN
    UPDATE SET
        tgt.expiration_date = CURRENT_DATE,
        tgt.is_current      = FALSE,
        tgt.updated_at      = CURRENT_TIMESTAMP;

-- 3b: Insert new version for changed records + brand-new customers
-- (Run as a separate statement after the MERGE above)
INSERT INTO dim_customer (
    customer_sk, customer_id, first_name, last_name, email,
    customer_segment, city, state, country,
    effective_date, expiration_date, is_current,
    created_at, updated_at, loaded_at
)
SELECT
    -- In production, use a sequence or identity column for customer_sk
    NEXT VALUE FOR customer_sk_seq,
    s.customer_id,
    s.first_name,
    s.last_name,
    s.email,
    s.customer_segment,
    s.city,
    s.state,
    s.country,
    CURRENT_DATE       AS effective_date,
    NULL               AS expiration_date,   -- NULL = current record
    TRUE               AS is_current,
    CURRENT_TIMESTAMP  AS created_at,
    CURRENT_TIMESTAMP  AS updated_at,
    CURRENT_TIMESTAMP  AS loaded_at
FROM staged AS s
LEFT JOIN current_dim AS c
    ON s.customer_id = c.customer_id
WHERE c.customer_sk IS NULL                   -- brand-new customer
   OR s.attribute_hash <> c.attribute_hash;   -- changed customer (new version)
