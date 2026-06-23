/*
    Intermediate: Unified Sales

    Cleaned/typed sales line items. Selects from staged sales and applies
    only type enforcement and null handling — no joins to other intermediate
    models. Foreign-key integrity (customer_id, product_id) is enforced by
    dbt relationships tests, not by joins at query time.

    Materialized as a table (see dbt_project.yml: intermediate +materialized: table).
*/

select
    cast(sale_line_id as varchar)   as sale_line_id,
    cast(sale_id as varchar)        as sale_id,
    cast(customer_id as varchar)    as customer_id,
    cast(product_id as varchar)     as product_id,
    cast(amount as double)          as amount,
    cast(stage as varchar)          as stage,
    cast(close_date as date)        as close_date,
    cast(created_at as timestamp)   as created_at,
    current_timestamp               as loaded_at
from {{ ref('transactions__sales') }}
