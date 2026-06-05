/*
    Intermediate: Unified Products

    Unions staged product records from Acme and Globe into a single schema.
    Business logic applied here:
      - Acme has stock_qty but no cost data; Globe has unit_cost but no stock_qty.
      - Acme availability derived from stock_qty > 0; Globe already staged as boolean.
      - Surrogate key generated from source_system + source ID.
*/

with acme_products as (

    select
        'acme'                                          as source_system,
        product_id                                      as source_product_id,
        product_name,
        product_description,
        product_category,
        retail_price,
        cast(null as double)                            as unit_cost,
        stock_quantity,
        case
            when stock_quantity > 0 then true
            else false
        end                                             as is_available,
        created_at
    from {{ ref('stg_acme__inventory') }}

),

globe_products as (

    select
        'globe'                                         as source_system,
        product_id                                      as source_product_id,
        product_name,
        product_description,
        product_category,
        retail_price,
        unit_cost,
        cast(null as integer)                           as stock_quantity,
        is_available,
        created_at
    from {{ ref('stg_globe__products') }}

),

unioned as (

    select * from acme_products
    union all
    select * from globe_products

)

select
    {{ dbt_utils.generate_surrogate_key(['source_system', 'source_product_id']) }}
                                                        as product_sk,
    source_system,
    source_product_id,
    product_name,
    product_description,
    product_category,
    retail_price,
    unit_cost,
    stock_quantity,
    is_available,
    created_at,
    current_timestamp                                   as loaded_at
from unioned
