/*
    Staging: Globe CRM Products

    1:1 with the raw source table. Renames columns to canonical names
    and casts types. No business logic applied here.
*/

select
    cast(prod_id as varchar)        as product_id,
    product_title                   as product_name,
    product_desc                    as product_description,
    product_type                    as product_category,
    unit_cost,
    retail_price,
    case
        when available = 1 then true
        else false
    end                             as is_available,
    cast(created_at as date)        as created_at
from {{ source('raw_globe', 'raw_globe__products') }}
