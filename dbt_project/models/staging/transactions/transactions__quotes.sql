/*
    Staging: Transactions Quotes

    1:1 with the raw source table. Raw column names are already canonical,
    so this casts types only — no renames, no business logic.
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
    cast(created_at as timestamp)   as created_at
from {{ source('transactions', 'transactions__quotes') }}
