{% test change_tracking_enabled(model) %}
{% if execute %}
    {%- set results = run_query(
        "SHOW TABLES LIKE '"
        ~ (model.identifier | upper)
        ~ "' IN SCHEMA "
        ~ model.database
        ~ "."
        ~ model.schema
    ) -%}
    {%- set ns = namespace(tracking_on=false) -%}
    {%- for row in results -%}
        {%- if row['change_tracking'] | string | upper == 'ON' -%}
            {%- set ns.tracking_on = true -%}
        {%- endif -%}
    {%- endfor -%}
    {% if ns.tracking_on %}
select null as table_name where false
    {% else %}
select '{{ model.identifier }}' as table_name
    {% endif %}
{% else %}
select null as table_name where false
{% endif %}
{% endtest %}
