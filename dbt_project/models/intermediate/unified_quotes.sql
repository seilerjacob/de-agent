/*
    Intermediate: Unified Quotes

    Cleaned/typed quote line items. Selects from staged quotes and applies
    only type enforcement and null handling — no joins to other intermediate
    models. Foreign-key integrity (customer_id, product_id) is enforced by
    dbt relationships tests, not by joins at query time.

    Materialized as a table (see dbt_project.yml: intermediate +materialized: table).
*/

select
    cast(quote_line_id as varchar)  as quote_line_id,
    cast(quote_id as varchar)       as quote_id,
    cast(customer_id as varchar)    as customer_id,
    cast(product_id as varchar)     as product_id,
    cast(quoted_price as double)    as quoted_price,
    cast(quantity as integer)       as quantity,
    cast(status as varchar)         as status,
    cast(expiry_date as date)       as expiry_date,
    cast(created_at as timestamp)   as created_at,
    current_timestamp               as loaded_at
from {{ ref('transactions__quotes') }}
