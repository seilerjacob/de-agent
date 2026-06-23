/*
    Staging: Acme CRM Inventory

    1:1 with the raw source table. Renames columns to canonical names
    and casts types. No business logic applied here.
*/

select
    cast(item_id as varchar)        as product_id,
    item_name                       as product_name,
    item_description                as product_description,
    category                        as product_category,
    price                           as retail_price,
    stock_qty                       as stock_quantity,
    cast(added_date as date)        as created_at
from {{ source('acme', 'acme__inventory') }}
