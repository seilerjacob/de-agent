/*
    Staging: Globe CRM Customers

    1:1 with the raw source table. Renames columns to canonical names
    and casts types. No business logic applied here.
*/

select
    cast(cust_id as varchar)        as customer_id,
    full_name,
    email,
    mobile_phone                    as phone_number,
    organization,
    status,
    cast(signup_date as date)       as created_at
from {{ source('raw_globe', 'raw_globe__customers') }}
