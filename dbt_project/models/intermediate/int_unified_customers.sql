/*
    Intermediate: Unified Customers

    Unions staged customer records from Acme and Globe into a single schema.
    Business logic applied here:
      - Acme has separate first/last name; Globe has full_name → derive both forms.
      - Acme has no status field → default to 'active'.
      - Surrogate key generated from source_system + source ID.

    Materialized as a Snowflake Dynamic Table: Snowflake auto-refreshes it as
    upstream data changes, within the target_lag window — no dbt scheduler
    needed for the refresh cycle. See docs/reference-snowflake.md.
*/

{{ config(
    materialized='dynamic_table',
    target_lag='1 minute',
    snowflake_warehouse=env_var('SNOWFLAKE_WAREHOUSE')
) }}

with acme_customers as (

    select
        'acme'                                          as source_system,
        contact_id                                      as source_customer_id,
        first_name,
        last_name,
        first_name || ' ' || last_name                  as full_name,
        email,
        phone_number,
        organization,
        'active'                                        as status,
        created_at
    from {{ ref('stg_acme__contacts') }}

),

globe_customers as (

    select
        'globe'                                         as source_system,
        customer_id                                     as source_customer_id,
        split_part(full_name, ' ', 1)                   as first_name,
        case
            when contains(full_name, ' ')
            then substr(full_name, position(' ' in full_name) + 1)
            else null
        end                                             as last_name,
        full_name,
        email,
        phone_number,
        organization,
        status,
        created_at
    from {{ ref('stg_globe__customers') }}

),

unioned as (

    select * from acme_customers
    union all
    select * from globe_customers

)

select
    {{ dbt_utils.generate_surrogate_key(['source_system', 'source_customer_id']) }}
                                                        as customer_sk,
    source_system,
    source_customer_id,
    first_name,
    last_name,
    full_name,
    email,
    phone_number,
    organization,
    status,
    created_at,
    current_timestamp                                   as loaded_at
from unioned
