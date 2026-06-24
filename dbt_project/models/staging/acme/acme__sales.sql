/*
    Staging: Acme Sales

    1:1 with the raw source table. Raw column names are already canonical,
    so this casts types only — no renames, no business logic.
*/

select
    cast(sale_line_id as varchar)   as sale_line_id,
    cast(sale_id as varchar)        as sale_id,
    cast(customer_id as varchar)    as customer_id,
    cast(product_id as varchar)     as product_id,
    cast(amount as double)          as amount,
    cast(stage as varchar)          as stage,
    cast(close_date as date)        as close_date,
    cast(created_at as timestamp)   as created_at
from {{ source('acme', 'acme__sales') }}
