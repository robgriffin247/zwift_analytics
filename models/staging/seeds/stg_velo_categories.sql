with 

source as (
    select
        category::varchar as category,
        womens::boolean as womens,
        min::int as min,
        max::int as max
    from {{ ref("velo_categories")}}
)

select * from source