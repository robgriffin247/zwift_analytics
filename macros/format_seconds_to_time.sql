{% macro format_seconds_to_time(total_seconds) -%}
    (
        lpad((cast(floor(cast(floor({{ total_seconds }} * 1000) as bigint) / 3600000) as bigint))::varchar, 2, '0')
        || ':' ||
        lpad((cast(floor((cast(floor({{ total_seconds }} * 1000) as bigint) % 3600000) / 60000) as bigint))::varchar, 2, '0')
        || ':' ||
        lpad((cast(floor((cast(floor({{ total_seconds }} * 1000) as bigint) % 60000) / 1000) as bigint))::varchar, 2, '0')
        || '.' ||
        lpad(((cast(floor({{ total_seconds }} * 1000) as bigint) % 1000))::varchar, 3, '0')
    )
{%- endmacro %}
