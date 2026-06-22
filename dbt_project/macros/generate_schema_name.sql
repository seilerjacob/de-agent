{#
    Use the custom schema name verbatim instead of dbt's default
    "<target_schema>_<custom_schema>" concatenation.

    This lands the medallion layers in clean, predictable Snowflake
    schemas — STAGING and INTERMEDIATE — alongside the RAW schema that the
    Python ingestion layer writes to. Without this override, models would
    land in STAGING_STAGING / STAGING_INTERMEDIATE, which the pipeline
    summary step and the reference docs would then have to special-case.

    Models with no +schema set fall back to the profile's target schema.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema | trim }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
