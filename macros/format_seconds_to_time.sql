{% macro format_seconds_to_time(total_seconds, show_hours=true) -%}
    (
        {%- if show_hours -%}
        lpad((cast(floor(cast(floor({{ total_seconds }} * 1000) as bigint) / 3600000) as bigint))::varchar, 2, '0')
        || ':' ||
        lpad((cast(floor((cast(floor({{ total_seconds }} * 1000) as bigint) % 3600000) / 60000) as bigint))::varchar, 2, '0')
        {%- else -%}
        lpad((cast(floor(cast(floor({{ total_seconds }} * 1000) as bigint) / 60000) as bigint))::varchar, 2, '0')
        {%- endif -%}
        || ':' ||
        lpad((cast(floor((cast(floor({{ total_seconds }} * 1000) as bigint) % 60000) / 1000) as bigint))::varchar, 2, '0')
        || '.' ||
        lpad(((cast(floor({{ total_seconds }} * 1000) as bigint) % 1000))::varchar, 3, '0')
    )
{%- endmacro %}
