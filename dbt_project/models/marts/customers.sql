/*
    Mart: Customers

    Canonical, consumer-facing customer dimension. Selects from
    unified_customers and deduplicates on email so that a customer who
    appears in both Acme and Globe resolves to a single record.

    Tiebreaker: when the same email exists in both source systems, the
    Acme record is retained. 'acme' sorts before 'globe' alphabetically,
    so `order by source_system` achieves this without a case expression.
    Product decision: Acme is the system of record for customer identity
    when conflicts exist.

    Materialized as a view (see dbt_project.yml: marts +materialized: view):
    zero storage cost, always reflects current unified_customers data.
*/

{{ config(materialized='view') }}

with ranked as (

    select
        *,
        row_number() over (
            partition by lower(email)
            order by source_system
        ) as rn
    from {{ ref('unified_customers') }}

)

select
    customer_sk     as customer_id,
    first_name,
    last_name,
    full_name,
    email,
    phone_number,
    organization,
    status,
    source_system,
    created_at,
    loaded_at
from ranked
where rn = 1
