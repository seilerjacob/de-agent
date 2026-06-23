/*
    Staging: Acme CRM Contacts

    1:1 with the raw source table. Renames columns to canonical names
    and casts types. No business logic applied here.
*/

select
    cast(contact_id as varchar)     as contact_id,
    first_name,
    last_name,
    email_address                   as email,
    phone                           as phone_number,
    company_name                    as organization,
    cast(created_date as date)      as created_at
from {{ source('acme', 'acme__contacts') }}
